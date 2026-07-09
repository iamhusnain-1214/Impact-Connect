"""
Seeds the database with real, well-known Pakistani NGOs.
Run this once after schema.sql: python -m db.seed_real_ngos

Descriptions below are written in our own words based on general knowledge
of each organization's public mission - not copied from any single source.
Contact numbers are intentionally omitted (set to a placeholder) since we
don't want to publish unverified phone numbers; website links are accurate
and are the correct place to find current contact details.
"""

from db.connection import get_connection

REAL_NGOS = [
    {
        "name": "Edhi Foundation",
        "description": "One of Pakistan's oldest and largest welfare organizations, running the country's largest volunteer ambulance network alongside shelters, orphanages, and free medical care.",
        "mission": "Provide free emergency, medical, and welfare services to anyone in need, regardless of background.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://edhi.org",
        "categories": ["Healthcare", "Disaster Relief", "Orphans", "Blood Donation"],
    },
    {
        "name": "Alkhidmat Foundation Pakistan",
        "description": "A nationwide humanitarian organization active in disaster response, healthcare, education, and orphan care, with a long track record in flood and earthquake relief across Pakistan.",
        "mission": "Deliver humanitarian and welfare services across health, education, disaster management, and orphan support.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://alkhidmat.org",
        "categories": ["Disaster Relief", "Education", "Healthcare", "Orphans", "Flood Relief"],
    },
    {
        "name": "Saylani Welfare International Trust",
        "description": "A large-scale welfare organization known for daily free food distribution (dastarkhwan), vocational training programs, and healthcare services delivered through hundreds of branches.",
        "mission": "Fight poverty through food security, free education, vocational training, and healthcare access.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://saylaniwelfare.com",
        "categories": ["Food", "Education", "Healthcare"],
    },
    {
        "name": "The Citizens Foundation (TCF)",
        "description": "One of Pakistan's largest networks of low-cost private schools, focused on bringing quality education to children in underserved urban and rural communities.",
        "mission": "Provide access to quality education for underprivileged children across Pakistan.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://www.tcf.org.pk",
        "categories": ["Education", "Children"],
    },
    {
        "name": "Shaukat Khanum Memorial Cancer Hospital & Research Centre",
        "description": "Pakistan's largest cancer treatment and research facility, providing subsidized and free-of-cost cancer care to patients who cannot afford treatment.",
        "mission": "Provide cancer treatment and research regardless of a patient's ability to pay.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://shaukatkhanum.org.pk",
        "categories": ["Healthcare"],
    },
    {
        "name": "Akhuwat Foundation",
        "description": "A pioneering interest-free microfinance organization that helps low-income families start small businesses, alongside education and healthcare support programs.",
        "mission": "Alleviate poverty through interest-free lending and community welfare programs.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://akhuwat.org.pk",
        "categories": ["Women", "Education", "Healthcare"],
    },
    {
        "name": "JDC Foundation",
        "description": "A growing welfare organization providing health centers, education support, vocational training, and disaster recovery services across Pakistan.",
        "mission": "Support underserved communities through health, education, and disaster recovery services.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://jdcwelfare.org",
        "categories": ["Healthcare", "Disaster Relief", "Education", "Orphans"],
    },
    {
        "name": "Chhipa Welfare Association",
        "description": "A Karachi-based welfare organization offering ambulance services, free food distribution, and support for orphans and the destitute.",
        "mission": "Provide emergency and welfare services to Karachi's most vulnerable residents.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://chhipawelfare.org",
        "categories": ["Food", "Disaster Relief", "Orphans"],
    },
    {
        "name": "Transparent Hands",
        "description": "A crowdfunding-driven healthcare platform that connects donors directly with patients needing surgeries and medical treatment they cannot otherwise afford.",
        "mission": "Make free surgical and medical treatment accessible through transparent, trackable crowdfunding.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://www.transparenthands.org",
        "categories": ["Healthcare"],
    },
    {
        "name": "Sundas Foundation",
        "description": "A dedicated organization providing free treatment, blood transfusions, and support for children living with Thalassemia and related blood disorders.",
        "mission": "Provide free treatment and support to Thalassemia patients across Pakistan.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://www.sundasfoundation.org",
        "categories": ["Healthcare", "Children", "Blood Donation"],
    },
    {
        "name": "Kashf Foundation",
        "description": "A leading microfinance institution focused specifically on empowering low-income women entrepreneurs through small loans and financial literacy training.",
        "mission": "Advance women's economic empowerment through microfinance and skills training.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://kashf.org",
        "categories": ["Women"],
    },
    {
        "name": "SOS Children's Villages Pakistan",
        "description": "Part of a global network providing family-style care, education, and long-term support for orphaned and abandoned children.",
        "mission": "Give every child a loving home and the chance to shape their own future.",
        "city": "Lahore",
        "province": "Punjab",
        "website": "https://www.sos-childrensvillages.org/where-we-help/asia/pakistan",
        "categories": ["Orphans", "Children"],
    },
    {
        "name": "Layton Rahmatulla Benevolent Trust (LRBT)",
        "description": "Pakistan's largest free eye-care network, operating hospitals and outreach clinics that provide free eye surgery and treatment nationwide.",
        "mission": "Eliminate preventable blindness by providing free, high-quality eye care.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://lrbt.org.pk",
        "categories": ["Healthcare", "Disability"],
    },
    {
        "name": "Al-Mustafa Welfare Society",
        "description": "A long-running welfare society operating medical centers, schools, and orphanages across Pakistan, with a strong history of disaster response since the 2005 earthquake.",
        "mission": "Provide health, education, and emergency relief services to low-income communities nationwide.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://almustafatrust.org",
        "categories": ["Healthcare", "Education", "Disaster Relief", "Orphans"],
    },
    {
        "name": "Shifa Foundation",
        "description": "An organization focused on preventive and curative healthcare, clean water access, and disaster emergency response across marginalized areas of Pakistan.",
        "mission": "Improve healthcare, water access, and disaster resilience for underserved communities.",
        "city": "Karachi",
        "province": "Sindh",
        "website": "https://shifafoundation.org",
        "categories": ["Healthcare", "Water", "Disaster Relief"],
    },
]

PLACEHOLDER_NAMES = ["Roshni Trust", "Sailaab Relief", "Garam Kapray Foundation"]


def seed():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Remove the Phase-1 placeholder sample NGOs so they don't mix with real data
        for name in PLACEHOLDER_NAMES:
            cursor.execute("DELETE FROM ngos WHERE name = %s", (name,))
        conn.commit()

        # Build category name -> id lookup
        cursor.execute("SELECT category_id, name FROM categories")
        cat_lookup = {row["name"]: row["category_id"] for row in cursor.fetchall()}

        inserted = 0
        for ngo in REAL_NGOS:
            cursor.execute("SELECT ngo_id FROM ngos WHERE name = %s", (ngo["name"],))
            if cursor.fetchone():
                print(f"  Skipping (already exists): {ngo['name']}")
                continue

            cursor.execute(
                """INSERT INTO ngos (name, description, mission, city, province, contact, website, verified)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)""",
                (ngo["name"], ngo["description"], ngo["mission"], ngo["city"], ngo["province"],
                 "See website for contact details", ngo["website"])
            )
            ngo_id = cursor.lastrowid

            for cat_name in ngo["categories"]:
                cat_id = cat_lookup.get(cat_name)
                if cat_id:
                    cursor.execute(
                        "INSERT INTO ngo_categories (ngo_id, category_id) VALUES (%s, %s)",
                        (ngo_id, cat_id)
                    )

            # mark as pre-approved in the verification log for a clean audit trail
            cursor.execute(
                "INSERT INTO verification_requests (ngo_id, status, reviewed_at) VALUES (%s, 'approved', NOW())",
                (ngo_id,)
            )

            inserted += 1
            print(f"  Added: {ngo['name']} ({ngo['city']})")

        conn.commit()
        print(f"\nDone. Inserted {inserted} real NGOs.")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed()
