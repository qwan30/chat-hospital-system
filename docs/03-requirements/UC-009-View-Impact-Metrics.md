# UC-009: View Impact Metrics

## Metadata
- **ID:** UC-009
- **Bounded Context:** AI Summary / Operations
- **Related BR:** BR-005
- **Status:** draft
- **Owner:** Product Owner
- **Last updated:** 2026-06-07

## Actor
Product Manager (PM), Hospital Administrator

## Trigger
Actor navigates to the Impact Metrics Dashboard (SCR-024).

## Preconditions
- User is authenticated
- User has "Administrator", "PM", or "Product Owner" role

## Main Flow
1. User navigates to the Impact Metrics Dashboard (SCR-024).
2. System calls the `GET /api/v1/metrics/summary` API to fetch aggregated performance data.
3. System computes savings based on baseline metrics:
   - Average manual patient review time baseline = 15 minutes (900 seconds)
   - Average manual query time baseline = 5 minutes (300 seconds)
   - Clinician average hourly rate baseline = $75/hour
4. System calculates cumulative time saved: `(Count(Summaries) * (900s - Avg(Summary_Gen_Time))) + (Count(Queries) * (300s - Avg(Query_Response_Time)))`.
5. System calculates cumulative cost savings: `(Total_Time_Saved_Hours * 75)`.
6. System displays: Total Time Saved, Estimated Cost Savings, Total AI Interactions, Citation Rate (%), Safe Refusal Rate (%), and Thumbs Up/Down Retrieval Accuracy (%).
7. User filters metrics by date range (e.g., last 7 days, 30 days) or department.

## Alternative Flows
- **7a. Adjust baseline settings:** User updates default manual baseline parameters (e.g., changes hourly rate to $90/hour) → System re-computes cost savings dynamically and updates dashboard charts.

## Exceptions
- **E1. Unauthorized role access:** Authenticated user without PM/Admin role attempts to load the metrics dashboard → System returns HTTP 403 Forbidden.
- **E2. No metric events found:** No queries or summaries have been run in the selected date range → System displays dashboard layout with "0" values and "No interaction data available for this range."

## Postconditions
- Aggregated, de-identified productivity metrics are rendered in graphical dashboard charts
- No Protected Health Information (PHI) is exposed in the dashboard query payloads

## Acceptance Criteria

### AC-1: Metrics dashboard accessibility
**Given:** An authenticated user with the role "PM"  
**When:** The user navigates to the Impact Metrics Dashboard (SCR-024)  
**Then:** System renders the metrics dashboard with charts  
**And:** API request to `GET /api/v1/metrics/summary` returns HTTP 200 OK  

### AC-2: Time and cost savings calculations
**Given:** System has recorded exactly 10 patient summaries (average generation time 10s) and 100 chat queries (average response time 2s)  
**When:** Productivity metrics dashboard is loaded  
**Then:** Cumulative time saved is calculated as: `(10 * (900 - 10)) + (100 * (300 - 2)) = 8,900 + 29,800 = 38,700 seconds` (10.75 hours)  
**And:** Cost savings display is exactly `10.75 * 75 = $806.25`  

### AC-3: Data de-identification check
**Given:** Clinician queries contain patient names and medical conditions  
**When:** PM views the dashboard analytics list or exports dataset  
**Then:** The raw query text and patient IDs are completely omitted from the metrics payload  
**And:** Only aggregated counts, durations, and feedback categories are returned  

## Dependencies
- **Upstream UC:** None
- **Downstream UC:** None
- **External Systems:** PostgreSQL Analytics Database

## Notes
Calculations rely on de-identified metadata logged during chat and summary executions. Under no circumstances should PHI leak into the analytics database.

## History
- v1 (2026-06-07, Agent): Created template with 3 ACs
