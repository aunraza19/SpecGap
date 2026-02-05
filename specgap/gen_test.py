from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'SpecGap Confidential Test Data', 0, 1, 'C')
        self.ln(10)

def create_pdf(filename, title, content):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title, 0, 1, 'L')
    pdf.ln(5)
    
    # Content
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, content)
    
    pdf.output(filename)
    print(f"✅ Generated: {filename}")

# --- DOCUMENT 1: The "Humble" Tech Spec ---
# This describes a weak, cheap, single-server system.
tech_spec_content = """
1. SYSTEM OVERVIEW
This document defines the MVP architecture for the 'LegacyApp' project.
Due to budget constraints, the system is designed for low-cost hosting.

2. ARCHITECTURE
- Server: Single AWS t2.micro instance.
- Database: SQLite file stored locally on the server disk.
- Redundancy: None. If the server crashes, the site goes down.
- Load Balancing: Not applicable (Direct IP connection).

3. AUTHENTICATION
- User passwords are stored in the local database.
- No 2FA or SSO implementation is planned for Phase 1.

4. API LIMITS
- The server can handle approximately 10 concurrent users.
- Requests exceeding this limit will time out.
"""

# --- DOCUMENT 2: The "Salesy" Proposal ---
# This promises the moon, contradicting the spec above.
proposal_content = """
1. EXECUTIVE SUMMARY
We are proud to propose the 'FutureScale' Enterprise Platform.
This solution is designed for mission-critical operations requiring maximum reliability.

2. PERFORMANCE GUARANTEES
- Uptime SLA: 99.999% (Five Nines).
- High Availability: Automated failover across 3 Availability Zones.
- Capacity: Supports 50,000+ concurrent users with auto-scaling.

3. SECURITY & COMPLIANCE
- SOC2 Type II Compliant.
- Enterprise SSO (Okta/Azure AD) included.
- All data is encrypted at rest and in transit.

4. PRICING TERMS
- Total Cost: $150,000 / year.
- The Vendor reserves the right to increase pricing by unlimited % annually.
- All intellectual property (IP) developed remains the sole property of the Vendor.
"""

if __name__ == "__main__":
    create_pdf("tech_spec.pdf", "Technical Specification (MVP)", tech_spec_content)
    create_pdf("proposal.pdf", "Business Proposal (Final)", proposal_content)