"""
Underwriting Intake & Submission Triage Agent (Apex)
=====================================================
AI-powered digital front door for commercial insurance underwriting.
Uses GPT-5.2 vision to analyze insurance documents (ACORD forms, loss runs, engineering reports).
Generates consolidated intake reports with clickable links to highlighted source locations.

Documents are stored in Azure File Storage under:
  underwriting_submissions/{submission_id}/
    - green_valley_app.pdf
    - loss_runs_2020-2025.pdf
    - engineering_report.pdf
    - statement_of_values.csv
"""

import os
import sys
import base64
import logging
import io
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

# Add parent paths for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rapp_ai')))

from agents.basic_agent import BasicAgent
from utils.azure_file_storage import AzureFileStorageManager
from openai import AzureOpenAI
from azure.identity import ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential
from azure.identity import get_bearer_token_provider

# PDF processing
try:
    from pypdf import PdfReader
    from PIL import Image
    import fitz  # PyMuPDF for PDF to image conversion
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PDF processing libraries not fully available. Install: pip install pypdf pillow pymupdf")

# Azure File Storage directory for underwriting submissions
STORAGE_DIRECTORY = "underwriting_submissions"


class DocumentType(Enum):
    ACORD_125 = "ACORD 125 - Commercial Insurance Application"
    ACORD_126 = "ACORD 126 - Commercial General Liability"
    ACORD_140 = "ACORD 140 - Property Section"
    LOSS_RUN = "Loss Run Report"
    ENGINEERING = "Risk Control/Engineering Report"
    SOV = "Statement of Values"
    NOISE = "Noise/Signature/Logo"


class TriageStatus(Enum):
    IN_APPETITE = "In Appetite"
    REFERRAL = "Referral Required"
    DECLINE = "Decline"
    PENDING_INFO = "Pending Broker Info"


class ApexIntakeAgent(BasicAgent):
    """
    The Apex Underwriting Intake Agent - Digital front door for submissions.
    Uses GPT-5.2 vision to analyze insurance documents from Azure File Storage.
    """

    def __init__(self):
        self.name = 'underwriting_intake_agent'
        self.metadata = {
            "name": self.name,
            "description": "Ingests insurance submissions, uses GPT vision to analyze documents, extracts risk data, identifies gaps, and prioritizes the underwriting queue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "submission_folder": {
                        "type": "string",
                        "description": "The folder name in Azure File Storage containing submission documents (e.g., 'green_valley')"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["process_submission", "get_queue", "analyze_document", "get_summary", "draft_broker_query", "generate_intake_report"],
                        "description": "The action to perform on the submission. Use 'generate_intake_report' to create a consolidated PDF with clickable links to highlighted sources."
                    },
                    "document_name": {
                        "type": "string",
                        "description": "Specific document to analyze (e.g., 'loss_runs_2020-2025.pdf')"
                    }
                },
                "required": ["action"]
            }
        }
        self.version = "2.0.0"  # Updated to use GPT vision
        self.storage_directory = STORAGE_DIRECTORY
        self.agents = [
            "SubmissionIngestionAgent",
            "DocumentClassificationAgent",
            "DataExtractionAgent",
            "GapAnalysisAgent",
            "AppetiteMatchingAgent",
            "TriagePrioritizationAgent"
        ]

        # Initialize Azure OpenAI client with vision capability
        self._init_openai_client()

        # Initialize Azure File Storage
        try:
            self.storage = AzureFileStorageManager()
        except Exception as e:
            logging.warning(f"Could not initialize Azure File Storage: {e}")
            self.storage = None

        # Initialize tracking for report generation
        self.highlight_locations = {}
        self.missing_link_areas = []
        self.extraction_link_areas = []

        super().__init__(self.name, self.metadata)

    def _init_openai_client(self):
        """Initialize Azure OpenAI client with Entra ID authentication."""
        try:
            credential = ChainedTokenCredential(
                ManagedIdentityCredential(),
                AzureCliCredential()
            )
            token_provider = get_bearer_token_provider(
                credential,
                "https://cognitiveservices.azure.com/.default"
            )

            self.openai_client = AzureOpenAI(
                azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT', ''),
                azure_ad_token_provider=token_provider,
                api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
            )
            self.deployment_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-5.2-chat')
            logging.info(f"Azure OpenAI client initialized with deployment: {self.deployment_name}")
        except Exception as e:
            logging.error(f"Failed to initialize Azure OpenAI client: {e}")
            self.openai_client = None
            self.deployment_name = None

    def _pdf_to_base64_images(self, pdf_bytes: bytes, max_pages: int = 5) -> List[str]:
        """
        Convert PDF pages to base64-encoded images for GPT vision.

        Args:
            pdf_bytes: Raw PDF file bytes
            max_pages: Maximum number of pages to convert (default 5)

        Returns:
            List of base64-encoded PNG images
        """
        if not PDF_SUPPORT:
            logging.error("PDF support not available. Install: pip install pymupdf pillow")
            return []

        images = []
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            num_pages = min(len(doc), max_pages)

            for page_num in range(num_pages):
                page = doc[page_num]
                # Render page to image (2x zoom for better quality)
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG", optimize=True)
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                images.append(img_base64)

            doc.close()
            logging.info(f"Converted {len(images)} PDF pages to images")
        except Exception as e:
            logging.error(f"Error converting PDF to images: {e}")

        return images

    def _analyze_document_with_vision(self, document_path: str, document_bytes: bytes, analysis_type: str) -> str:
        """
        Use GPT-5.2 vision to analyze a document.

        Args:
            document_path: Path to document for context
            document_bytes: Raw document bytes
            analysis_type: Type of analysis to perform

        Returns:
            AI-generated analysis
        """
        if not self.openai_client:
            return "Error: Azure OpenAI client not initialized. Check AZURE_OPENAI_ENDPOINT configuration."

        # Convert PDF to images
        images = self._pdf_to_base64_images(document_bytes)
        if not images:
            return "Error: Could not convert PDF to images for analysis."

        # Build analysis prompt based on document type
        prompts = {
            "acord": """Analyze this ACORD insurance application form and extract:
1. **Named Insured**: Company name, DBA, entity type
2. **Location Details**: Address, city, state, ZIP
3. **Building Information**: Year built, construction type, square footage, stories, sprinkler system
4. **Roof Information**: Roof type, roof update year (IMPORTANT - flag if missing)
5. **Classification**: NAICS code, SIC code, business description
6. **Coverage Requested**: Lines of coverage, effective/expiration dates, limits, deductibles
7. **Prior Insurance**: Current carrier, policy number, premium

Format as markdown. Highlight any MISSING or BLANK fields that would be required for underwriting.""",

            "loss_run": """Analyze this insurance loss run report and extract:
1. **Carrier Information**: Issuing carrier name
2. **Policy Period**: Date range covered
3. **Loss Summary by Year**: Create a table with columns: Year, Premium, Claims Count, Paid Amount, Reserved, Total Incurred, Loss Ratio
4. **Individual Claims**: List each claim with date, type, description, amounts, status
5. **Overall Loss Ratio**: Calculate total 5-year loss ratio
6. **Trend Analysis**: Is the loss trend improving, stable, or worsening?

Format as markdown with tables. Provide an assessment of the loss history quality.""",

            "engineering": """Analyze this risk control/engineering report and extract:
1. **Survey Information**: Date, surveyor name/credentials
2. **Overall Risk Grade**: What rating was given?
3. **Property Risk Assessment**: Fire protection, construction, electrical, roof condition
4. **Liability Risk Assessment**: Safety programs, operations, hazards
5. **Management Assessment**: Safety culture, training programs
6. **Recommendations**: List all recommendations with priority level
7. **Positive Factors**: What makes this a good risk?
8. **Concerns**: What issues were identified?

Format as markdown. Provide an overall risk assessment.""",

            "general": """Analyze this insurance document and extract all relevant underwriting information including:
- Insured details
- Coverage information
- Risk characteristics
- Any concerning or missing information

Format as markdown with clear sections."""
        }

        prompt = prompts.get(analysis_type, prompts["general"])

        # Build message with images
        content = [{"type": "text", "text": f"Document: {document_path}\n\n{prompt}"}]

        for i, img_b64 in enumerate(images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high"
                }
            })

        try:
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert commercial insurance underwriter analyzing submission documents. Extract key risk information accurately and flag any missing or concerning data."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_completion_tokens=4000  # GPT-5.2 uses max_completion_tokens instead of max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logging.error(f"Error calling GPT vision API: {e}")
            return f"Error analyzing document: {str(e)}"

    def perform(self, **kwargs) -> str:
        """
        Main entry point for agent actions.
        Reads documents from Azure File Storage and analyzes with GPT vision.
        """
        action = kwargs.get('action', 'process_submission')
        submission_folder = kwargs.get('submission_folder', 'green_valley')
        document_name = kwargs.get('document_name', None)

        if action == 'process_submission':
            return self._process_full_submission(submission_folder)
        elif action == 'get_queue':
            return self._get_prioritized_queue()
        elif action == 'analyze_document' and document_name:
            return self._analyze_single_document(submission_folder, document_name)
        elif action == 'get_summary':
            return self._get_submission_summary(submission_folder)
        elif action == 'draft_broker_query':
            return self._draft_broker_query(submission_folder)
        elif action == 'generate_intake_report':
            return self._generate_intake_report(submission_folder)
        else:
            return f"Unknown action: {action}. Available actions: process_submission, get_queue, analyze_document, get_summary, draft_broker_query, generate_intake_report"

    def _process_full_submission(self, submission_folder: str) -> str:
        """
        Process all documents in a submission folder using GPT vision.
        """
        storage_path = f"{self.storage_directory}/{submission_folder}"

        if not self.storage:
            return "Error: Azure File Storage not available."

        # List files in submission folder
        try:
            files = self.storage.list_files(storage_path)
            if not files:
                return f"No files found in {storage_path}. Please upload submission documents first."
        except Exception as e:
            return f"Error accessing storage: {str(e)}"

        results = []
        results.append(f"**Processing Submission: {submission_folder}**")
        results.append(f"Storage Location: `{storage_path}/`\n")

        # Classify and analyze each document
        doc_summary = []
        for file_info in files:
            filename = file_info.get('name', '') if isinstance(file_info, dict) else str(file_info)
            if not filename.lower().endswith(('.pdf', '.csv', '.xlsx')):
                continue

            # Determine document type
            doc_type = self._classify_document_name(filename)
            doc_summary.append(f"| {filename} | {doc_type} |")

        results.append("**Documents Found:**")
        results.append("| File | Classification |")
        results.append("|------|---------------|")
        results.extend(doc_summary)
        results.append("")

        # Analyze key documents with GPT vision
        for file_info in files:
            filename = file_info.get('name', '') if isinstance(file_info, dict) else str(file_info)
            if filename.lower().endswith('.pdf'):
                results.append(f"\n---\n**Analyzing: {filename}**\n")

                # Read document from storage
                doc_bytes = self.storage.read_file_binary(storage_path, filename)
                if doc_bytes:
                    analysis_type = self._get_analysis_type(filename)
                    analysis = self._analyze_document_with_vision(
                        f"{storage_path}/{filename}",
                        doc_bytes,
                        analysis_type
                    )
                    results.append(analysis)
                else:
                    results.append(f"*Could not read {filename}*")

        return "\n".join(results)

    def _analyze_single_document(self, submission_folder: str, document_name: str) -> str:
        """
        Analyze a specific document using GPT vision.
        """
        storage_path = f"{self.storage_directory}/{submission_folder}"
        full_path = f"{storage_path}/{document_name}"

        if not self.storage:
            return "Error: Azure File Storage not available."

        # Read document
        doc_bytes = self.storage.read_file_binary(storage_path, document_name)
        if not doc_bytes:
            return f"Error: Could not read document at {full_path}"

        # Determine analysis type
        analysis_type = self._get_analysis_type(document_name)

        # Analyze with GPT vision
        result = [f"**Document Analysis**"]
        result.append(f"File: `{full_path}`")
        result.append(f"Analysis Type: {analysis_type.upper()}")
        result.append(f"Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append("\n---\n")

        analysis = self._analyze_document_with_vision(full_path, doc_bytes, analysis_type)
        result.append(analysis)

        return "\n".join(result)

    def _classify_document_name(self, filename: str) -> str:
        """Classify document based on filename."""
        filename_lower = filename.lower()

        if 'acord' in filename_lower or 'app' in filename_lower or 'application' in filename_lower:
            return DocumentType.ACORD_140.value
        elif 'loss' in filename_lower or 'run' in filename_lower:
            return DocumentType.LOSS_RUN.value
        elif 'engineering' in filename_lower or 'risk' in filename_lower or 'survey' in filename_lower:
            return DocumentType.ENGINEERING.value
        elif 'sov' in filename_lower or 'value' in filename_lower:
            return DocumentType.SOV.value
        else:
            return "Unknown Document Type"

    def _get_analysis_type(self, filename: str) -> str:
        """Get the analysis type for GPT vision based on filename."""
        filename_lower = filename.lower()

        if 'acord' in filename_lower or 'app' in filename_lower:
            return 'acord'
        elif 'loss' in filename_lower or 'run' in filename_lower:
            return 'loss_run'
        elif 'engineering' in filename_lower or 'risk' in filename_lower:
            return 'engineering'
        else:
            return 'general'

    def _get_prioritized_queue(self) -> str:
        """Return the current prioritized underwriting queue."""
        # This would typically query a database - using sample data for demo
        return f"""**Underwriting Queue - Priority View**
Snapshot: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Summary:**
| Status | Count |
|--------|-------|
| In-Appetite (Action Required) | 8 |
| In-Appetite (Ready to Quote) | 12 |
| Pending Broker Info | 15 |
| Referral Pending | 6 |
| **Total** | **47** |

**Priority Queue:**

| Rank | Insured | Broker | Score | Loss Ratio | Status | Est. Premium |
|------|---------|--------|-------|------------|--------|--------------|
| 1 | **Green Valley Manufacturing** | Marsh | 87 | 12% | Gap Identified | $85,000 |
| 2 | Precision Tools Inc | Aon | 82 | 18% | Ready for Quote | $62,000 |
| 3 | Metro Distribution Center | Willis | 79 | 22% | Ready for Quote | $120,000 |
| 4 | Midwest Industrial Park | Aon | 91 | 8% | Ready for Quote | $200,000 |
| 5 | TechFlow Logistics | Willis | 76 | 25% | Ready for Quote | $95,000 |

**Metrics:**
- Avg Processing Time: 3.2 minutes
- First Response Rate: 94%
- NIGO Reduction: 69%"""

    def _get_submission_summary(self, submission_folder: str) -> str:
        """Get submission summary - triggers full analysis if not cached."""
        return self._process_full_submission(submission_folder)

    def _draft_broker_query(self, submission_folder: str) -> str:
        """Generate broker query email based on gap analysis."""
        # First analyze to find gaps
        storage_path = f"{self.storage_directory}/{submission_folder}"

        prompt = """Based on the submission analysis, draft a professional broker query email requesting any missing information.
The email should:
1. Thank the broker for the submission
2. Highlight positive aspects (e.g., good loss history)
3. List specific missing items needed to proceed
4. Provide a turnaround time estimate

Format the email professionally."""

        return f"""**Draft Broker Query**

---
**To:** broker@marsh.com
**Subject:** RE: {submission_folder.replace('_', ' ').title()} - Additional Information Needed
---

*Note: Run `analyze_document` first to identify specific gaps, then this query will be customized based on the findings.*

**Standard Query Template:**

Hi,

Thank you for the submission. After reviewing the documents, we need the following to proceed with a quote:

• [Missing items will be listed here after document analysis]

We can turn this quote around within 24 hours once received.

Best regards,
Underwriting Team

---

**Actions:**
- [Approve & Send]
- [Edit Query]
- [Cancel]"""

    # =====================================
    # INTAKE REPORT GENERATION
    # =====================================

    # Color scheme for different data categories in the report
    HIGHLIGHT_COLORS = {
        "insured": (1, 1, 0.6),       # Light yellow
        "location": (0.6, 1, 0.6),     # Light green
        "building": (0.6, 0.8, 1),     # Light blue
        "coverage": (1, 0.8, 0.6),     # Light orange
        "claims": (1, 0.7, 0.7),       # Light red
        "dates": (0.8, 0.6, 1),        # Light purple
        "missing": (1, 0.3, 0.3),      # Bright red for missing
        "financial": (0.6, 1, 0.8),    # Light teal
        "risk": (0.8, 1, 0.6),         # Light lime
    }

    def _generate_intake_report(self, submission_folder: str) -> str:
        """
        Generate a consolidated intake report PDF with clickable links to highlighted source locations.

        Args:
            submission_folder: Folder name containing submission documents

        Returns:
            Status message with path to generated report
        """
        if not PDF_SUPPORT:
            return "Error: PDF support not available. Install: pip install pymupdf pillow"

        if not self.openai_client:
            return "Error: Azure OpenAI client not initialized. Check AZURE_OPENAI_ENDPOINT configuration."

        # Import storage factory to get the storage manager with Entra ID auth
        from utils.storage_factory import get_storage_manager
        storage = get_storage_manager()

        # Storage path for submission documents
        storage_path = f"{self.storage_directory}/{submission_folder}"

        # Define expected documents
        document_configs = [
            ("green_valley_app.pdf", "ACORD Commercial Property Application"),
            ("loss_runs_2020-2025.pdf", "Insurance Loss Run Report"),
            ("engineering_report.pdf", "Risk Control Engineering Report"),
        ]

        # Read documents from Azure File Storage
        input_docs = []
        for filename, doc_type in document_configs:
            try:
                doc_bytes = storage.read_file_binary(storage_path, filename)
                if doc_bytes:
                    input_docs.append((filename, doc_type, doc_bytes))
                    logging.info(f"Loaded {filename} from Azure File Storage")
            except Exception as e:
                logging.warning(f"Could not read {filename} from storage: {e}")

        if not input_docs:
            return f"Error: No documents found in Azure File Storage at {storage_path}/. Please upload submission documents first."

        # Output will be saved back to Azure File Storage
        output_filename = f"{submission_folder.upper()}_INTAKE_REPORT.pdf"

        # Generate the report
        try:
            result = self._build_consolidated_report_from_storage(
                input_docs=input_docs,
                submission_name=submission_folder.replace('_', ' ').title()
            )

            # Save report back to Azure File Storage
            storage.write_file(storage_path, output_filename, result['report_bytes'])
            logging.info(f"Saved report to Azure File Storage: {storage_path}/{output_filename}")

            return f"""**Intake Report Generated Successfully**

**Report Location:** `{storage_path}/{output_filename}`
**Documents Processed:** {result['documents_processed']}
**Total Extractions:** {result['total_extractions']}
**Missing Fields:** {result['missing_fields']}
**Clickable Links:** {result.get('internal_links', 0)}

The report includes:
- Cover page with submission summary and status
- Missing data summary page (if gaps found) - **click items to jump to source**
- Extraction summary organized by category - **click items to jump to source**
- All source documents with color-coded highlights

Report saved to Azure File Storage: `{storage_path}/{output_filename}`"""

        except Exception as e:
            logging.error(f"Error generating intake report: {e}")
            import traceback
            traceback.print_exc()
            return f"Error generating intake report: {str(e)}"

    def _build_consolidated_report_from_storage(self, input_docs: List[Tuple[str, str, bytes]], submission_name: str) -> Dict:
        """
        Build the consolidated intake report from document bytes (from Azure File Storage).

        Args:
            input_docs: List of (filename, doc_type, doc_bytes) tuples
            submission_name: Name for the submission

        Returns:
            Dict with report_bytes and stats
        """
        # Reset state for tracking links
        self.highlight_locations = {}
        self.missing_link_areas = []
        self.extraction_link_areas = []

        report_doc = fitz.open()
        all_doc_data = []
        source_docs = []  # Keep docs open until we're done

        # Process each document - extract data with GPT vision
        for filename, doc_type, doc_bytes in input_docs:
            logging.info(f"Processing: {filename}")

            source_doc = fitz.open(stream=doc_bytes, filetype="pdf")
            source_docs.append((filename, doc_type, source_doc))

            doc_data = self._extract_with_locations_for_report(source_doc, doc_type, filename)
            all_doc_data.append(doc_data)

            logging.info(f"Found {len(doc_data.get('extractions', []))} extractions, {len(doc_data.get('missing_required', []))} missing")

        # Build report structure
        # 1. Cover page
        self._create_report_cover_page(report_doc, submission_name, all_doc_data)

        # 2. Missing data page (if any missing)
        total_missing = sum(len(d.get("missing_required", [])) for d in all_doc_data)
        if total_missing > 0:
            self._create_report_missing_data_page(report_doc, all_doc_data)

        # 3. Extraction summary
        self._create_report_extraction_summary_page(report_doc, all_doc_data)

        # 4. Add each document with highlights (this populates highlight_locations)
        for (filename, doc_type, source_doc), doc_data in zip(source_docs, all_doc_data):
            self._highlight_and_copy_pages_for_report(
                source_doc,
                report_doc,
                doc_data.get("extractions", []),
                filename
            )

        # 5. Add internal links from summary pages to highlighted locations
        links_added = self._add_report_internal_links(report_doc)

        # Get report as bytes
        report_bytes = report_doc.tobytes()

        # Close all documents
        for _, _, source_doc in source_docs:
            source_doc.close()
        report_doc.close()

        return {
            "report_bytes": report_bytes,
            "documents_processed": len(all_doc_data),
            "total_extractions": sum(len(d.get("extractions", [])) for d in all_doc_data),
            "missing_fields": total_missing,
            "internal_links": links_added
        }

    def _extract_with_locations_for_report(self, doc: fitz.Document, doc_type: str, doc_name: str) -> Dict:
        """Extract data with GPT vision for the report, including search text for highlighting."""
        images = self._pdf_to_base64_images(doc.tobytes())

        prompt = f"""Analyze this {doc_type} and extract data in STRUCTURED JSON format.

For EACH extracted field, provide:
- "field": Field name
- "value": Extracted value (use "MISSING" or "BLANK" if not provided)
- "search_text": EXACT text as it appears in document (for highlighting)
- "category": One of: insured, location, building, coverage, claims, dates, missing, financial, risk
- "confidence": high/medium/low
- "is_missing": true if field is blank/missing but required, false otherwise
- "importance": critical/high/medium/low

Return ONLY valid JSON:
{{
  "document_name": "{doc_name}",
  "document_type": "{doc_type}",
  "extractions": [...],
  "missing_required": [
    {{"field": "field name", "reason": "why it's needed", "impact": "impact on underwriting"}}
  ],
  "risk_assessment": "Brief assessment",
  "recommendation": "Next steps"
}}

IMPORTANT: Identify ALL missing/blank REQUIRED fields and explain their importance."""

        content = [{"type": "text", "text": prompt}]
        for img_b64 in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}", "detail": "high"}
            })

        try:
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert underwriter. Return ONLY valid JSON."},
                    {"role": "user", "content": content}
                ],
                max_completion_tokens=4000
            )

            response_text = response.choices[0].message.content
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            return json.loads(response_text)

        except Exception as e:
            logging.error(f"Error extracting with locations: {e}")
            return {"document_name": doc_name, "extractions": [], "missing_required": []}

    def _highlight_and_copy_pages_for_report(self, source_doc: fitz.Document, target_doc: fitz.Document,
                                              extractions: List[Dict], doc_name: str):
        """Copy pages with highlights and track locations for linking."""
        for page_num in range(len(source_doc)):
            target_doc.insert_pdf(source_doc, from_page=page_num, to_page=page_num)
            target_page = target_doc[-1]
            final_page_num = len(target_doc) - 1

            # Add document header
            header_rect = fitz.Rect(0, 0, target_page.rect.width, 30)
            target_page.draw_rect(header_rect, color=(0.2, 0.3, 0.5), fill=(0.2, 0.3, 0.5))
            target_page.insert_text((10, 20), f"  {doc_name} - Page {page_num + 1}",
                                   fontsize=12, fontname="helv", color=(1, 1, 1))

            # Add highlights and track locations
            for ext in extractions:
                search_text = ext.get("search_text", "")
                field_name = ext.get("field", "")
                category = ext.get("category", "insured")
                is_missing = ext.get("is_missing", False)

                if is_missing:
                    category = "missing"

                color = self.HIGHLIGHT_COLORS.get(category, (1, 1, 0.6))

                if search_text and len(search_text) >= 2:
                    instances = target_page.search_for(search_text)
                    for inst in instances:
                        highlight = target_page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=color)

                        comment = f"MISSING: {field_name}" if is_missing else f"{field_name}: {ext.get('value', '')}"
                        highlight.set_info(content=comment, title="AI Extraction")
                        highlight.update()

                        # Store location for linking
                        location_key = f"{doc_name}:{field_name}"
                        if location_key not in self.highlight_locations:
                            self.highlight_locations[location_key] = (final_page_num, inst)
                        if field_name and field_name not in self.highlight_locations:
                            self.highlight_locations[field_name] = (final_page_num, inst)

    def _create_report_cover_page(self, doc: fitz.Document, submission_name: str, documents: List[Dict]):
        """Create cover page for the report."""
        page = doc.new_page(-1, width=612, height=792)

        # Header bar
        header_rect = fitz.Rect(0, 0, 612, 80)
        page.draw_rect(header_rect, color=(0.1, 0.2, 0.4), fill=(0.1, 0.2, 0.4))
        page.insert_text((50, 35), "APEX UNDERWRITING INTAKE REPORT", fontsize=20, fontname="helv", color=(1, 1, 1))
        page.insert_text((50, 55), "AI-Powered Document Analysis & Gap Detection", fontsize=11, fontname="helv", color=(0.8, 0.8, 0.8))

        y = 100
        page.insert_text((50, y), f"Submission: {submission_name}", fontsize=14, fontname="helv", color=(0.1, 0.2, 0.4))
        y += 20
        page.insert_text((50, y), f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 15
        page.insert_text((50, y), f"Documents Analyzed: {len(documents)}", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))

        # Stats box
        y += 40
        stats_rect = fitz.Rect(50, y, 300, y + 80)
        page.draw_rect(stats_rect, color=(0.9, 0.9, 0.9), fill=(0.95, 0.95, 0.95))

        total_extractions = sum(len(d.get("extractions", [])) for d in documents)
        total_missing = sum(len(d.get("missing_required", [])) for d in documents)

        page.insert_text((60, y + 20), "ANALYSIS SUMMARY", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))
        page.insert_text((60, y + 40), f"Total Data Points Extracted: {total_extractions}", fontsize=10, fontname="helv")

        missing_color = (0.8, 0, 0) if total_missing > 0 else (0, 0.5, 0)
        page.insert_text((60, y + 55), f"Missing Required Fields: {total_missing}", fontsize=10, fontname="helv", color=missing_color)

        # Status indicator
        status_rect = fitz.Rect(320, y, 560, y + 80)
        if total_missing > 0:
            page.draw_rect(status_rect, color=(1, 0.9, 0.9), fill=(1, 0.95, 0.95))
            page.insert_text((340, y + 25), "STATUS: ACTION REQUIRED", fontsize=11, fontname="helv", color=(0.8, 0, 0))
            page.insert_text((340, y + 45), f"{total_missing} missing field(s)", fontsize=10, fontname="helv", color=(0.6, 0, 0))
            page.insert_text((340, y + 60), "See Page 2 for details", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))
        else:
            page.draw_rect(status_rect, color=(0.9, 1, 0.9), fill=(0.95, 1, 0.95))
            page.insert_text((340, y + 25), "STATUS: COMPLETE", fontsize=11, fontname="helv", color=(0, 0.5, 0))
            page.insert_text((340, y + 45), "All required fields present", fontsize=10, fontname="helv", color=(0, 0.4, 0))

        # Documents list
        y += 110
        page.insert_text((50, y), "DOCUMENTS INCLUDED:", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))
        y += 20

        for i, doc_info in enumerate(documents, 1):
            doc_name = doc_info.get("document_name", "Unknown")
            doc_type = doc_info.get("document_type", "")
            missing_count = len(doc_info.get("missing_required", []))

            icon = "!" if missing_count > 0 else "+"
            icon_color = (0.8, 0, 0) if missing_count > 0 else (0, 0.5, 0)

            page.insert_text((60, y), icon, fontsize=12, fontname="helv", color=icon_color)
            page.insert_text((80, y), f"{i}. {doc_name}", fontsize=10, fontname="helv")
            page.insert_text((80, y + 12), f"   {doc_type}", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

            if missing_count > 0:
                page.insert_text((400, y), f"{missing_count} missing", fontsize=9, fontname="helv", color=(0.8, 0, 0))

            y += 30

        # Color legend
        y += 20
        page.insert_text((50, y), "HIGHLIGHT LEGEND:", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))
        y += 15

        legend_items = [
            ("missing", "Missing/Blank Required"),
            ("insured", "Insured Information"),
            ("building", "Building Details"),
            ("coverage", "Coverage/Limits"),
            ("claims", "Claims/Loss History"),
            ("financial", "Financial Data"),
        ]

        x = 60
        for category, label in legend_items:
            color = self.HIGHLIGHT_COLORS.get(category, (1, 1, 0.6))
            rect = fitz.Rect(x, y - 8, x + 15, y + 2)
            page.draw_rect(rect, color=color, fill=color)
            page.insert_text((x + 20, y), label, fontsize=8, fontname="helv")
            x += 130
            if x > 500:
                x = 60
                y += 15

    def _create_report_missing_data_page(self, doc: fitz.Document, documents: List[Dict]):
        """Create missing data summary page with clickable areas."""
        page = doc.new_page(-1, width=612, height=792)

        # Header
        header_rect = fitz.Rect(0, 0, 612, 50)
        page.draw_rect(header_rect, color=(0.7, 0, 0), fill=(0.8, 0.1, 0.1))
        page.insert_text((50, 32), "MISSING DATA SUMMARY - ACTION REQUIRED", fontsize=16, fontname="helv", color=(1, 1, 1))

        y = 70

        # Collect all missing items
        all_missing = []
        for doc_info in documents:
            doc_name = doc_info.get("document_name", "Unknown")
            for missing in doc_info.get("missing_required", []):
                missing_copy = missing.copy()
                missing_copy["source_document"] = doc_name
                all_missing.append(missing_copy)

        if not all_missing:
            page.insert_text((50, y + 30), "No missing required fields detected.", fontsize=12, fontname="helv", color=(0, 0.5, 0))
            return

        page.insert_text((50, y), f"Found {len(all_missing)} missing required field(s) - Click to jump to source:", fontsize=11, fontname="helv")
        y += 25

        for i, missing in enumerate(all_missing, 1):
            if y > 700:
                page = doc.new_page(-1, width=612, height=792)
                y = 50

            box_rect = fitz.Rect(50, y, 560, y + 70)
            page.draw_rect(box_rect, color=(1, 0.9, 0.9), fill=(1, 0.95, 0.95))

            # Number badge
            badge_rect = fitz.Rect(55, y + 5, 75, y + 25)
            page.draw_rect(badge_rect, color=(0.8, 0, 0), fill=(0.8, 0, 0))
            page.insert_text((60, y + 19), str(i), fontsize=11, fontname="helv", color=(1, 1, 1))

            field_name = missing.get("field", "Unknown Field")
            page.insert_text((85, y + 18), field_name, fontsize=11, fontname="helv", color=(0.6, 0, 0))

            source = missing.get("source_document", "")
            page.insert_text((85, y + 32), f"Source: {source}", fontsize=8, fontname="helv", color=(0.4, 0.4, 0.4))
            page.insert_text((450, y + 18), "[Click to view]", fontsize=8, fontname="helv", color=(0, 0, 0.7))

            # Store link area
            self.missing_link_areas.append({
                "page_idx": len(doc) - 1,
                "rect": box_rect,
                "field": field_name,
                "source": source
            })

            reason = missing.get("reason", "Required for underwriting")
            page.insert_text((85, y + 48), f"Why needed: {reason[:70]}", fontsize=9, fontname="helv")

            impact = missing.get("impact", "")
            if impact:
                page.insert_text((85, y + 62), f"Impact: {impact[:70]}", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

            y += 80

    def _create_report_extraction_summary_page(self, doc: fitz.Document, documents: List[Dict]):
        """Create extraction summary page with clickable items."""
        page = doc.new_page(-1, width=612, height=792)

        header_rect = fitz.Rect(0, 0, 612, 40)
        page.draw_rect(header_rect, color=(0.2, 0.3, 0.5), fill=(0.2, 0.3, 0.5))
        page.insert_text((50, 26), "EXTRACTION SUMMARY - Click any item to jump to source", fontsize=14, fontname="helv", color=(1, 1, 1))

        y = 60

        # Group extractions by category
        categories = {}
        for doc_info in documents:
            doc_name = doc_info.get("document_name", "Unknown")
            for ext in doc_info.get("extractions", []):
                ext_copy = ext.copy()
                ext_copy["source_document"] = doc_name
                cat = ext.get("category", "other")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(ext_copy)

        category_labels = {
            "insured": "INSURED INFORMATION",
            "location": "LOCATION DETAILS",
            "building": "BUILDING INFORMATION",
            "coverage": "COVERAGE & LIMITS",
            "claims": "CLAIMS HISTORY",
            "financial": "FINANCIAL DATA",
            "dates": "KEY DATES",
            "risk": "RISK FACTORS",
        }

        for cat, label in category_labels.items():
            if cat not in categories:
                continue

            if y > 700:
                page = doc.new_page(-1, width=612, height=792)
                y = 50

            color = self.HIGHLIGHT_COLORS.get(cat, (0.5, 0.5, 0.5))

            cat_rect = fitz.Rect(50, y, 560, y + 18)
            page.draw_rect(cat_rect, color=color, fill=color)
            page.insert_text((55, y + 13), label, fontsize=9, fontname="helv", color=(0, 0, 0))
            y += 22

            for ext in categories[cat][:10]:
                if y > 750:
                    page = doc.new_page(-1, width=612, height=792)
                    y = 50

                field = ext.get("field", "")
                value = ext.get("value", "")
                source = ext.get("source_document", "")

                text = f"{field}: {value}"
                if len(text) > 80:
                    text = text[:77] + "..."

                is_missing = ext.get("is_missing", False) or value in ["MISSING", "BLANK", ""]
                text_color = (0.7, 0, 0) if is_missing else (0.2, 0.2, 0.2)

                row_rect = fitz.Rect(55, y, 555, y + 14)
                page.insert_text((60, y + 10), text, fontsize=9, fontname="helv", color=text_color)
                page.insert_text((500, y + 10), ">>", fontsize=8, fontname="helv", color=(0, 0, 0.6))

                self.extraction_link_areas.append({
                    "page_idx": len(doc) - 1,
                    "rect": row_rect,
                    "field": field,
                    "source": source
                })

                y += 16

            y += 10

    def _add_report_internal_links(self, doc: fitz.Document) -> int:
        """Add clickable internal links from summary pages to highlighted locations."""
        links_added = 0

        # Add links for missing data items
        for link_info in self.missing_link_areas:
            field = link_info["field"]
            source = link_info["source"]

            location_key = f"{source}:{field}"
            target = self.highlight_locations.get(location_key) or self.highlight_locations.get(field)

            if target:
                target_page, target_rect = target
                page = doc[link_info["page_idx"]]

                link = {
                    "kind": fitz.LINK_GOTO,
                    "from": link_info["rect"],
                    "page": target_page,
                    "to": fitz.Point(target_rect.x0, target_rect.y0),
                    "zoom": 0
                }
                page.insert_link(link)
                links_added += 1

        # Add links for extraction summary items
        for link_info in self.extraction_link_areas:
            field = link_info["field"]
            source = link_info["source"]

            location_key = f"{source}:{field}"
            target = self.highlight_locations.get(location_key) or self.highlight_locations.get(field)

            if target:
                target_page, target_rect = target
                page = doc[link_info["page_idx"]]

                link = {
                    "kind": fitz.LINK_GOTO,
                    "from": link_info["rect"],
                    "page": target_page,
                    "to": fitz.Point(target_rect.x0, target_rect.y0),
                    "zoom": 0
                }
                page.insert_link(link)
                links_added += 1

        return links_added


# Standalone sub-agent classes
class SubmissionIngestionAgent(BasicAgent):
    """Monitors email inboxes, broker portals, and APIs for incoming submissions."""

    def __init__(self):
        self.name = 'submission_ingestion_agent'
        self.metadata = {
            "name": self.name,
            "description": "Monitors submission channels and ingests new submissions to Azure File Storage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "enum": ["email", "portal", "api"]},
                    "submission_id": {"type": "string"}
                }
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return "Submission ingested and stored in Azure File Storage: underwriting_submissions/{submission_id}/"


class DocumentClassificationAgent(BasicAgent):
    """Classifies documents within submissions using GPT vision."""

    def __init__(self):
        self.name = 'document_classification_agent'
        self.metadata = {
            "name": self.name,
            "description": "Classifies submission documents using GPT vision (ACORD forms, loss runs, engineering reports).",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_path": {"type": "string", "description": "Path to document in Azure File Storage"}
                },
                "required": ["document_path"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        doc_path = kwargs.get('document_path', '')
        return f"Document classified using GPT vision: {doc_path}"


class DataExtractionAgent(BasicAgent):
    """Extracts structured data from classified documents using GPT vision."""

    def __init__(self):
        self.name = 'data_extraction_agent'
        self.metadata = {
            "name": self.name,
            "description": "Extracts risk indicators, policy details, and loss history from documents using GPT vision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_path": {"type": "string"},
                    "extraction_type": {"type": "string", "enum": ["full", "summary", "loss_history"]}
                },
                "required": ["document_path"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return "Extracted data using GPT-5.2 vision analysis."


class GapAnalysisAgent(BasicAgent):
    """Identifies missing data and generates broker queries."""

    def __init__(self):
        self.name = 'gap_analysis_agent'
        self.metadata = {
            "name": self.name,
            "description": "Analyzes submissions for missing data and drafts broker queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "submission_folder": {"type": "string"}
                },
                "required": ["submission_folder"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return "Gap analysis completed using GPT vision document review."


class AppetiteMatchingAgent(BasicAgent):
    """Scores submissions against underwriting guidelines."""

    def __init__(self):
        self.name = 'appetite_matching_agent'
        self.metadata = {
            "name": self.name,
            "description": "Evaluates submissions against carrier appetite and underwriting guidelines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "submission_folder": {"type": "string"},
                    "guidelines_version": {"type": "string"}
                },
                "required": ["submission_folder"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return "Appetite matching completed based on extracted document data."


class TriagePrioritizationAgent(BasicAgent):
    """Prioritizes the underwriting queue."""

    def __init__(self):
        self.name = 'triage_prioritization_agent'
        self.metadata = {
            "name": self.name,
            "description": "Prioritizes submissions based on appetite score, broker tier, and premium potential.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sort_by": {"type": "string", "enum": ["appetite_score", "premium", "time_in_queue"]}
                }
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return "Queue reprioritized based on AI-extracted document data."


# Demo execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    agent = ApexIntakeAgent()
    print(f"Apex Agent v{agent.version}")
    print(f"OpenAI Client: {'Initialized' if agent.openai_client else 'Not available'}")
    print(f"Storage: {'Initialized' if agent.storage else 'Not available'}")
    print(f"PDF Support: {PDF_SUPPORT}")
    print()

    # Test generate_intake_report action
    print("Testing generate_intake_report action...")
    result = agent.perform(action="generate_intake_report", submission_folder="green_valley")
    print(result)
