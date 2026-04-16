-- Vunoh Global — Task Assistant
-- Supabase / PostgreSQL schema

CREATE TABLE IF NOT EXISTS tasks (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_code           TEXT NOT NULL UNIQUE,
  original_message    TEXT NOT NULL,
  intent              TEXT NOT NULL,
  entities            JSONB DEFAULT '{}',
  risk_score          INTEGER NOT NULL DEFAULT 0,
  risk_label          TEXT NOT NULL DEFAULT 'low',
  risk_reasons        JSONB DEFAULT '[]',
  steps               JSONB DEFAULT '[]',
  employee_assignment TEXT NOT NULL,
  status              TEXT NOT NULL DEFAULT 'Pending'
                        CHECK (status IN ('Pending', 'In Progress', 'Completed')),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status    ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_intent    ON tasks(intent);
CREATE INDEX IF NOT EXISTS idx_tasks_created   ON tasks(created_at DESC);

-- ── Messages ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS task_messages (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id           UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  whatsapp_message  TEXT,
  email_message     TEXT,
  sms_message       TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_task ON task_messages(task_id);

-- ── Auto-update updated_at ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_tasks_updated_at ON tasks;
CREATE TRIGGER trg_tasks_updated_at
  BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ── Sample data ───────────────────────────────────────────────────────────────
 

INSERT INTO tasks (task_code, original_message, intent, entities, risk_score, risk_label, risk_reasons, steps, employee_assignment, status, created_at)
VALUES

(
  'VNH-A1B2C3',
  'I need to send KES 50,000 to my father in Mombasa urgently. His name is James Odhiambo.',
  'send_money',
  '{"amount": "KES 50000", "recipient": "James Odhiambo", "location": "Mombasa", "urgency": "urgent"}',
  60,
  'high',
  '["Transfer above KES 50,000 requires recipient verification", "Urgency flag raises risk — rushed transfers are a common fraud vector"]',
  '[{"step_number":1,"title":"Verify sender identity","description":"Confirm the sender''s identity via their registered phone number and ID.","owner":"Finance Team"},{"step_number":2,"title":"Confirm recipient details","description":"Verify James Odhiambo''s phone number and bank or M-Pesa details in Mombasa.","owner":"Finance Team"},{"step_number":3,"title":"Initiate transfer","description":"Process the KES 50,000 transfer through the approved payment rail.","owner":"System"},{"step_number":4,"title":"Send confirmation","description":"Notify both sender and recipient with transaction reference number.","owner":"System"}]',
  'Finance Team',
  'Completed',
  NOW() - INTERVAL '3 days'
),

(
  'VNH-D4E5F6',
  'Please verify my land title deed for the plot I own in Karen, Nairobi. I need to confirm it has not been fraudulently transferred.',
  'verify_document',
  '{"document_type": "land title deed", "location": "Karen, Nairobi", "notes": "Check for fraudulent transfer"}',
  65,
  'high',
  '["Land title verification is high-risk due to fraud prevalence in Kenya", "Land title verification carries elevated legal risk"]',
  '[{"step_number":1,"title":"Receive document copy","description":"Customer submits a scanned copy of the title deed via the platform.","owner":"Customer"},{"step_number":2,"title":"Search at Lands Registry","description":"Legal team conducts an official search at the Nairobi Lands Registry.","owner":"Legal Team"},{"step_number":3,"title":"Cross-check encumbrances","description":"Check for any cautions, caveats, or encumbrances registered against the title.","owner":"Legal Team"},{"step_number":4,"title":"Issue verification report","description":"Prepare and send a formal verification report to the customer.","owner":"Legal Team"}]',
  'Legal Team',
  'In Progress',
  NOW() - INTERVAL '1 day'
),

(
  'VNH-G7H8I9',
  'Can someone clean my apartment in Westlands every Friday? I have a two-bedroom flat.',
  'hire_service',
  '{"service_type": "cleaning", "location": "Westlands, Nairobi", "service_date": "every Friday", "notes": "Two-bedroom flat"}',
  18,
  'low',
  '[]',
  '[{"step_number":1,"title":"Match service provider","description":"Identify a vetted cleaner available in Westlands on Fridays.","owner":"Operations Team"},{"step_number":2,"title":"Send provider profile","description":"Share cleaner''s profile and rates with the customer for approval.","owner":"Operations Team"},{"step_number":3,"title":"Schedule first visit","description":"Confirm the first cleaning date and share access instructions.","owner":"Customer"},{"step_number":4,"title":"Completion sign-off","description":"Customer confirms completion after each visit via the platform.","owner":"Customer"}]',
  'Operations Team',
  'Pending',
  NOW() - INTERVAL '6 hours'
),

(
  'VNH-J1K2L3',
  'Book an airport transfer from JKIA to Kilimani for my mother arriving this Saturday at 6am. Flight KQ101.',
  'airport_transfer',
  '{"recipient": "customer''s mother", "location": "JKIA to Kilimani", "service_date": "Saturday 6am", "notes": "Flight KQ101"}',
  13,
  'low',
  '[]',
  '[{"step_number":1,"title":"Confirm flight details","description":"Verify flight KQ101 arrival time with the airline or flight tracker.","owner":"Logistics Team"},{"step_number":2,"title":"Assign driver","description":"Assign a vetted driver with a suitable vehicle for the route.","owner":"Logistics Team"},{"step_number":3,"title":"Send driver details","description":"Share driver name, vehicle plate, and contact number with the customer.","owner":"System"},{"step_number":4,"title":"Confirm pickup","description":"Driver confirms pickup at the arrivals hall and drops passenger safely.","owner":"Logistics Team"}]',
  'Logistics Team',
  'Pending',
  NOW() - INTERVAL '2 hours'
),

(
  'VNH-M4N5O6',
  'I need a lawyer to review a rental agreement for a property on Ngong Road. The landlord wants to sign next week.',
  'hire_service',
  '{"service_type": "legal consultation", "location": "Ngong Road, Nairobi", "service_date": "next week", "notes": "Rental agreement review"}',
  23,
  'low',
  '["No recipient or provider identified in request"]',
  '[{"step_number":1,"title":"Receive agreement document","description":"Customer uploads the rental agreement PDF to the platform.","owner":"Customer"},{"step_number":2,"title":"Assign advocate","description":"Match customer with a qualified advocate familiar with Kenyan tenancy law.","owner":"Legal Team"},{"step_number":3,"title":"Initial review","description":"Advocate reviews the agreement and flags any unusual or unfair clauses.","owner":"Legal Team"},{"step_number":4,"title":"Feedback to customer","description":"Lawyer provides written feedback and recommended amendments within 48 hours.","owner":"Legal Team"},{"step_number":5,"title":"Final sign-off","description":"Customer approves changes and proceeds to signing with landlord.","owner":"Customer"}]',
  'Legal Team',
  'Pending',
  NOW() - INTERVAL '30 minutes'
);


-- ── Messages for sample tasks ─────────────────────────────────────────────────

INSERT INTO task_messages (task_id, whatsapp_message, email_message, sms_message)
SELECT
  id,
  E'Hi! Your task has been received. 🎉\n\nTask code: VNH-A1B2C3\nAmount: KES 50,000 to James Odhiambo in Mombasa\n\nWe''re processing your transfer now. You''ll hear from us within the hour.',
  E'Dear Customer,\n\nThank you for using Vunoh Global. Your money transfer request has been received and assigned to our Finance Team.\n\nTask Code: VNH-A1B2C3\nAmount: KES 50,000\nRecipient: James Odhiambo, Mombasa\nRisk Level: High — enhanced verification required\n\nNext Steps:\n1. Our team will contact you to verify the recipient details.\n2. Transfer will be initiated once verification is complete.\n3. You will receive a transaction reference number upon completion.\n\nIf you have any questions, reply with your task code.\n\nWarm regards,\nVunoh Global Team',
  'VNH-A1B2C3: KES 50k transfer to Mombasa received. Finance team will call to verify recipient. Est. 1hr.'
FROM tasks WHERE task_code = 'VNH-A1B2C3';

INSERT INTO task_messages (task_id, whatsapp_message, email_message, sms_message)
SELECT
  id,
  E'Your land title verification is underway. 📋\n\nTask code: VNH-D4E5F6\nProperty: Karen, Nairobi\n\nOur legal team is conducting an official search at the Lands Registry. We''ll update you within 2 working days.',
  E'Dear Customer,\n\nYour request to verify a land title deed in Karen, Nairobi has been received and assigned to our Legal Team.\n\nTask Code: VNH-D4E5F6\nDocument Type: Land Title Deed\nLocation: Karen, Nairobi\nRisk Level: High — official registry search required\n\nNext Steps:\n1. Please submit a scanned copy of the title deed through the platform.\n2. Our advocate will conduct a formal search at the Nairobi Lands Registry.\n3. A written verification report will be issued within 2 working days.\n\nWarm regards,\nVunoh Global Team',
  'VNH-D4E5F6: Land title verification started. Legal team conducting registry search. Report in 2 days.'
FROM tasks WHERE task_code = 'VNH-D4E5F6';

INSERT INTO task_messages (task_id, whatsapp_message, email_message, sms_message)
SELECT
  id,
  E'Great news — we''re finding you a cleaner! 🧹\n\nTask code: VNH-G7H8I9\nService: Weekly cleaning, Westlands\nSchedule: Every Friday\n\nWe''ll send you a cleaner profile for approval before the first visit.',
  E'Dear Customer,\n\nYour request for a weekly cleaning service in Westlands has been received.\n\nTask Code: VNH-G7H8I9\nService: Apartment Cleaning (2-bedroom)\nLocation: Westlands, Nairobi\nSchedule: Every Friday\nRisk Level: Low\n\nNext Steps:\n1. Our Operations Team will identify a vetted cleaner in your area.\n2. We will send you their profile and rates for your approval.\n3. Once confirmed, we will schedule the first visit.\n\nWarm regards,\nVunoh Global Team',
  'VNH-G7H8I9: Weekly cleaning in Westlands requested. We will share a cleaner profile for approval shortly.'
FROM tasks WHERE task_code = 'VNH-G7H8I9';

INSERT INTO task_messages (task_id, whatsapp_message, email_message, sms_message)
SELECT
  id,
  E'Airport transfer booked! 🚗\n\nTask code: VNH-J1K2L3\nPickup: JKIA, Saturday 6am\nFlight: KQ101\n\nWe''ll send your driver''s details the evening before.',
  E'Dear Customer,\n\nYour airport transfer request has been received and is being arranged.\n\nTask Code: VNH-J1K2L3\nPickup Location: JKIA Arrivals\nDestination: Kilimani, Nairobi\nDate & Time: Saturday, 6:00 AM\nFlight: KQ101\nRisk Level: Low\n\nNext Steps:\n1. We will verify the flight arrival time.\n2. A vetted driver will be assigned to this route.\n3. Driver details will be sent to you the evening before pickup.\n\nWarm regards,\nVunoh Global Team',
  'VNH-J1K2L3: Transfer JKIA-Kilimani, Sat 6am. Driver details sent night before. Ref: KQ101.'
FROM tasks WHERE task_code = 'VNH-J1K2L3';

INSERT INTO task_messages (task_id, whatsapp_message, email_message, sms_message)
SELECT
  id,
  E'Your legal review request is in. ⚖️\n\nTask code: VNH-M4N5O6\nService: Rental agreement review, Ngong Road\n\nPlease upload the agreement document. Our advocate will review it within 48 hours.',
  E'Dear Customer,\n\nYour request for a rental agreement review has been received and assigned to our Legal Team.\n\nTask Code: VNH-M4N5O6\nService: Legal Consultation\nDocument: Rental Agreement\nLocation: Ngong Road, Nairobi\nRisk Level: Low\n\nNext Steps:\n1. Please upload the rental agreement document through the platform.\n2. An advocate will be assigned to review it.\n3. Written feedback with recommended amendments will be provided within 48 hours.\n\nWarm regards,\nVunoh Global Team',
  'VNH-M4N5O6: Rental agreement review requested. Upload your document to proceed. Advocate assigned.'
FROM tasks WHERE task_code = 'VNH-M4N5O6';
