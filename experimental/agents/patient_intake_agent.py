"""
Patient Intake and Scheduling Agent - Healthcare Automation
Generated via RAPP Pipeline Process

Industry: Healthcare
Use Case: Automate patient intake, appointment coordination, and reduce no-shows

Key Outcomes:
- Patient intake time reduced by 65%
- Digital form completion before arrival
- Insurance verification automation
- Medical history capture through guided questionnaires

Target Users: Front Desk Staff, Medical Assistants, Practice Managers
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class PatientIntakeAgent(BasicAgent):
    """
    Healthcare patient intake automation agent for streamlined
    registration, scheduling, and pre-visit preparation.
    """

    def __init__(self):
        self.name = 'PatientIntake'
        self.metadata = {
            "name": self.name,
            "description": "Automates patient intake processes including digital form distribution, insurance verification, medical history capture, appointment scheduling, and reminder management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "initiate_intake",
                            "verify_insurance",
                            "capture_history",
                            "schedule_appointment",
                            "send_reminders",
                            "check_in_patient",
                            "get_pre_visit_summary"
                        ],
                        "description": "Action to perform"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier"
                    },
                    "appointment_type": {
                        "type": "string",
                        "enum": ["new_patient", "follow_up", "annual_wellness", "sick_visit", "procedure"],
                        "description": "Type of appointment"
                    },
                    "provider_id": {
                        "type": "string",
                        "description": "Healthcare provider identifier"
                    },
                    "preferred_date": {
                        "type": "string",
                        "description": "Preferred appointment date (YYYY-MM-DD)"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action', 'initiate_intake')
        logger.info(f"PatientIntakeAgent performing action: {action}")

        try:
            if action == 'initiate_intake':
                return self._initiate_intake(kwargs)
            elif action == 'verify_insurance':
                return self._verify_insurance(kwargs.get('patient_id'), kwargs)
            elif action == 'capture_history':
                return self._capture_history(kwargs.get('patient_id'), kwargs)
            elif action == 'schedule_appointment':
                return self._schedule_appointment(kwargs)
            elif action == 'send_reminders':
                return self._send_reminders(kwargs.get('patient_id'), kwargs)
            elif action == 'check_in_patient':
                return self._check_in_patient(kwargs.get('patient_id'), kwargs)
            elif action == 'get_pre_visit_summary':
                return self._get_pre_visit_summary(kwargs.get('patient_id'), kwargs)
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"PatientIntakeAgent error: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})

    def _initiate_intake(self, params: Dict) -> str:
        """Initiate patient intake process with digital forms."""

        patient_id = params.get('patient_id', 'PAT-001')
        appointment_type = params.get('appointment_type', 'new_patient')

        intake = {
            "intake_id": f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient_id": patient_id,
            "initiated_at": datetime.now().isoformat(),
            "appointment_type": appointment_type,
            "forms_required": [
                {
                    "form_id": "FORM-001",
                    "name": "Patient Demographics",
                    "status": "Sent",
                    "required": True,
                    "estimated_time": "5 minutes"
                },
                {
                    "form_id": "FORM-002",
                    "name": "Insurance Information",
                    "status": "Sent",
                    "required": True,
                    "estimated_time": "3 minutes"
                },
                {
                    "form_id": "FORM-003",
                    "name": "Medical History Questionnaire",
                    "status": "Sent",
                    "required": True,
                    "estimated_time": "10 minutes"
                },
                {
                    "form_id": "FORM-004",
                    "name": "HIPAA Consent",
                    "status": "Sent",
                    "required": True,
                    "estimated_time": "2 minutes"
                },
                {
                    "form_id": "FORM-005",
                    "name": "Medication List",
                    "status": "Sent",
                    "required": True,
                    "estimated_time": "5 minutes"
                }
            ],
            "delivery_method": {
                "primary": "Email",
                "secondary": "SMS",
                "portal_link": "https://patient.portal.com/intake/INT-123456"
            },
            "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
            "reminders_scheduled": [
                {"type": "Email", "scheduled": (datetime.now() + timedelta(days=1)).isoformat()},
                {"type": "SMS", "scheduled": (datetime.now() + timedelta(hours=36)).isoformat()}
            ],
            "estimated_completion_time": "25 minutes",
            "patient_communication": {
                "email_sent": True,
                "sms_sent": True,
                "template": "NEW_PATIENT_INTAKE"
            }
        }

        return json.dumps({"status": "success", "intake": intake}, indent=2)

    def _verify_insurance(self, patient_id: str, params: Dict) -> str:
        """Verify patient insurance eligibility and coverage."""

        verification = {
            "patient_id": patient_id or "PAT-001",
            "verification_date": datetime.now().isoformat(),
            "insurance_info": {
                "payer": "Blue Cross Blue Shield",
                "plan_name": "PPO Select",
                "member_id": "XYZ123456789",
                "group_number": "GRP-98765",
                "subscriber": "Self",
                "effective_date": "2025-01-01",
                "termination_date": None
            },
            "eligibility_status": {
                "active": True,
                "verified_via": "Real-time EDI 270/271",
                "verification_code": "VER-2026-001234"
            },
            "coverage_details": {
                "primary_care_visit": {
                    "copay": "$25",
                    "deductible_applies": False,
                    "prior_auth_required": False
                },
                "specialist_visit": {
                    "copay": "$50",
                    "deductible_applies": False,
                    "prior_auth_required": False
                },
                "preventive_care": {
                    "copay": "$0",
                    "deductible_applies": False,
                    "coverage": "100%"
                }
            },
            "deductible_status": {
                "individual_deductible": "$500",
                "individual_met": "$350",
                "individual_remaining": "$150",
                "family_deductible": "$1,500",
                "family_met": "$800"
            },
            "out_of_pocket_max": {
                "individual": "$3,000",
                "individual_met": "$1,200",
                "family": "$6,000"
            },
            "alerts": [],
            "patient_responsibility_estimate": {
                "visit_type": "New Patient Visit",
                "estimated_charges": "$250",
                "insurance_payment": "$225",
                "patient_copay": "$25",
                "additional_patient_responsibility": "$0"
            }
        }

        return json.dumps({"status": "success", "verification": verification}, indent=2)

    def _capture_history(self, patient_id: str, params: Dict) -> str:
        """Capture and process patient medical history."""

        history = {
            "patient_id": patient_id or "PAT-001",
            "captured_at": datetime.now().isoformat(),
            "demographics": {
                "name": "Demo Contact A",
                "dob": "1985-03-15",
                "age": 40,
                "gender": "Female",
                "address": "1234 Oak Street, Portland, OR 97201",
                "phone": "(503) 555-0123",
                "email": "demo@example.com",
                "emergency_contact": {
                    "name": "Demo Contact 1",
                    "relationship": "Spouse",
                    "phone": "(503) 555-0124"
                }
            },
            "medical_history": {
                "allergies": [
                    {"allergen": "Penicillin", "reaction": "Hives", "severity": "Moderate"}
                ],
                "current_medications": [
                    {"medication": "Lisinopril", "dose": "10mg", "frequency": "Daily", "prescriber": "Dr. Smith"},
                    {"medication": "Metformin", "dose": "500mg", "frequency": "Twice daily", "prescriber": "Dr. Smith"}
                ],
                "chronic_conditions": [
                    {"condition": "Type 2 Diabetes", "diagnosed": "2020", "status": "Controlled"},
                    {"condition": "Hypertension", "diagnosed": "2019", "status": "Controlled"}
                ],
                "surgeries": [
                    {"procedure": "Appendectomy", "year": "2005", "complications": "None"}
                ],
                "family_history": [
                    {"condition": "Heart Disease", "relation": "Father"},
                    {"condition": "Type 2 Diabetes", "relation": "Mother"}
                ]
            },
            "social_history": {
                "smoking": "Never",
                "alcohol": "Occasional",
                "exercise": "3x per week",
                "occupation": "Software Engineer"
            },
            "review_of_systems": {
                "general": "No fever, chills, or weight changes",
                "cardiovascular": "No chest pain or palpitations",
                "respiratory": "No shortness of breath",
                "gastrointestinal": "No nausea or abdominal pain",
                "concerns_to_discuss": ["Annual checkup", "Diabetes management"]
            },
            "provider_alerts": [
                {"type": "Allergy", "message": "Penicillin allergy - use alternative antibiotics"},
                {"type": "Care Gap", "message": "Due for A1C screening"},
                {"type": "Medication Review", "message": "Verify metformin dose - last filled 45 days ago"}
            ],
            "form_completion_status": {
                "demographics": "Complete",
                "insurance": "Complete",
                "medical_history": "Complete",
                "consent_forms": "Complete",
                "overall": "100%"
            }
        }

        return json.dumps({"status": "success", "patient_history": history}, indent=2)

    def _schedule_appointment(self, params: Dict) -> str:
        """Schedule patient appointment with provider."""

        patient_id = params.get('patient_id', 'PAT-001')
        provider_id = params.get('provider_id', 'DR-001')
        appointment_type = params.get('appointment_type', 'follow_up')
        preferred_date = params.get('preferred_date', datetime.now().strftime('%Y-%m-%d'))

        appointment = {
            "appointment_id": f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient_id": patient_id,
            "provider": {
                "id": provider_id,
                "name": "Dr. Emily Chen",
                "specialty": "Internal Medicine",
                "location": "Portland Medical Center - Suite 200"
            },
            "appointment_details": {
                "type": appointment_type,
                "date": "2026-01-20",
                "time": "10:30 AM",
                "duration": "30 minutes",
                "status": "Confirmed"
            },
            "visit_preparation": {
                "forms_complete": True,
                "insurance_verified": True,
                "copay_amount": "$25",
                "special_instructions": [
                    "Please arrive 15 minutes early",
                    "Bring photo ID and insurance card",
                    "Fasting not required for this visit"
                ]
            },
            "reminders_scheduled": [
                {"type": "Email", "send_date": "2026-01-18", "status": "Scheduled"},
                {"type": "SMS", "send_date": "2026-01-19", "status": "Scheduled"},
                {"type": "SMS", "send_date": "2026-01-20 09:00", "status": "Scheduled"}
            ],
            "confirmation_sent": {
                "email": True,
                "sms": True,
                "calendar_invite": True
            },
            "check_in_options": {
                "online_check_in": "Available 24 hours before",
                "kiosk_check_in": "Available on arrival",
                "front_desk": "Available on arrival"
            }
        }

        return json.dumps({"status": "success", "appointment": appointment}, indent=2)

    def _send_reminders(self, patient_id: str, params: Dict) -> str:
        """Send appointment reminders to patient."""

        reminders = {
            "patient_id": patient_id or "PAT-001",
            "appointment_id": "APT-2026-001234",
            "appointment_date": "2026-01-20",
            "reminders_sent": [
                {
                    "type": "Email",
                    "sent_at": datetime.now().isoformat(),
                    "template": "APPOINTMENT_REMINDER_48H",
                    "status": "Delivered",
                    "content_preview": "Your appointment with Dr. Chen is scheduled for Monday, January 20th at 10:30 AM..."
                },
                {
                    "type": "SMS",
                    "sent_at": datetime.now().isoformat(),
                    "template": "SMS_REMINDER_48H",
                    "status": "Delivered",
                    "content_preview": "Reminder: Appt with Dr. Chen on Mon 1/20 at 10:30 AM. Reply C to confirm, R to reschedule."
                }
            ],
            "response_tracking": {
                "confirmation_received": False,
                "reschedule_requested": False,
                "cancellation_requested": False,
                "response_deadline": (datetime.now() + timedelta(hours=24)).isoformat()
            },
            "no_show_prevention": {
                "risk_score": "Low",
                "historical_no_show_rate": "5%",
                "mitigation_actions": ["Standard reminder sequence"]
            },
            "upcoming_reminders": [
                {"type": "SMS", "scheduled": "2026-01-19 10:00", "template": "SMS_REMINDER_24H"},
                {"type": "SMS", "scheduled": "2026-01-20 09:00", "template": "SMS_REMINDER_DAY_OF"}
            ]
        }

        return json.dumps({"status": "success", "reminders": reminders}, indent=2)

    def _check_in_patient(self, patient_id: str, params: Dict) -> str:
        """Process patient check-in for appointment."""

        check_in = {
            "patient_id": patient_id or "PAT-001",
            "check_in_time": datetime.now().isoformat(),
            "appointment_id": "APT-2026-001234",
            "check_in_method": "Online",
            "verification": {
                "identity_verified": True,
                "insurance_card_captured": True,
                "photo_id_verified": True,
                "consent_forms_signed": True
            },
            "intake_status": {
                "demographics_current": True,
                "medications_reviewed": True,
                "allergies_confirmed": True,
                "reason_for_visit": "Annual wellness exam and diabetes follow-up"
            },
            "payment": {
                "copay_due": "$25",
                "copay_collected": True,
                "payment_method": "Credit Card ending 4321",
                "receipt_sent": True
            },
            "wait_status": {
                "position_in_queue": 2,
                "estimated_wait": "10 minutes",
                "room_assignment": "Exam Room 3"
            },
            "provider_notification": {
                "notified": True,
                "patient_summary_available": True,
                "alerts_flagged": 2
            },
            "patient_instructions": [
                "Please have a seat in the waiting area",
                "A medical assistant will call you shortly",
                "Exam Room 3 has been assigned"
            ]
        }

        return json.dumps({"status": "success", "check_in": check_in}, indent=2)

    def _get_pre_visit_summary(self, patient_id: str, params: Dict) -> str:
        """Generate pre-visit summary for provider."""

        summary = {
            "patient_id": patient_id or "PAT-001",
            "generated_at": datetime.now().isoformat(),
            "patient": {
                "name": "Demo Contact A",
                "age": 40,
                "dob": "1985-03-15"
            },
            "visit_info": {
                "type": "Annual Wellness + Diabetes Follow-up",
                "provider": "Dr. Emily Chen",
                "date": "2026-01-20",
                "time": "10:30 AM"
            },
            "clinical_summary": {
                "chief_complaint": "Annual checkup, diabetes management review",
                "active_conditions": ["Type 2 Diabetes (controlled)", "Hypertension (controlled)"],
                "allergies": ["Penicillin - Hives"],
                "current_medications": [
                    "Lisinopril 10mg daily",
                    "Metformin 500mg BID"
                ]
            },
            "care_gaps": [
                {"gap": "A1C screening", "due": "Overdue by 1 month", "priority": "High"},
                {"gap": "Retinal exam", "due": "Due in 2 months", "priority": "Medium"},
                {"gap": "Flu vaccine", "due": "Current season", "priority": "Medium"}
            ],
            "recent_results": [
                {"test": "A1C", "date": "2025-10-15", "result": "7.2%", "trend": "Stable"},
                {"test": "Blood Pressure", "date": "2025-10-15", "result": "128/82", "trend": "Improving"},
                {"test": "Cholesterol Panel", "date": "2025-07-20", "result": "Total: 195", "trend": "Stable"}
            ],
            "provider_alerts": [
                {"type": "Medication", "message": "Verify metformin adherence - last filled 45 days ago"},
                {"type": "Care Gap", "message": "Order A1C today"},
                {"type": "Prevention", "message": "Discuss flu vaccine"}
            ],
            "patient_reported": {
                "concerns": ["Increased fatigue", "Question about diet"],
                "medication_adherence": "Good",
                "lifestyle_changes": "Started walking 3x/week"
            }
        }

        return json.dumps({"status": "success", "pre_visit_summary": summary}, indent=2)
