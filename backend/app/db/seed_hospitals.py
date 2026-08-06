"""
Seed the hospitals table with 50 real-ish Indian hospitals.
Run: python -m app.db.seed_hospitals
"""
import asyncio
from app.db.database import AsyncSessionLocal, init_db
from app.models.hospital import Hospital

HOSPITALS = [
    # Mumbai
    {"name": "Lilavati Hospital", "city": "Mumbai", "state": "Maharashtra",
     "address": "A-791, Bandra Reclamation, Bandra West, Mumbai - 400050",
     "phone": "022-26455555", "latitude": 19.0523, "longitude": 72.8246,
     "specialties": ["trauma", "cardiac", "neurology", "burn"],
     "icu_beds_available": 45, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.7},
    {"name": "Kokilaben Dhirubhai Ambani Hospital", "city": "Mumbai", "state": "Maharashtra",
     "address": "Rao Saheb Achutrao Patwardhan Marg, Four Bungalows, Andheri West",
     "phone": "022-42696969", "latitude": 19.1245, "longitude": 72.8356,
     "specialties": ["trauma", "cardiac", "neurology", "orthopedic", "burn"],
     "icu_beds_available": 80, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.0, "rating": 4.8},
    {"name": "Breach Candy Hospital", "city": "Mumbai", "state": "Maharashtra",
     "address": "60-A, Bhulabhai Desai Road, Breach Candy, Mumbai - 400026",
     "phone": "022-23667888", "latitude": 18.9717, "longitude": 72.8091,
     "specialties": ["cardiac", "trauma", "neurology"],
     "icu_beds_available": 30, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.5},
    {"name": "Hinduja Hospital", "city": "Mumbai", "state": "Maharashtra",
     "address": "Veer Savarkar Marg, Mahim, Mumbai - 400016",
     "phone": "022-24447000", "latitude": 19.0367, "longitude": 72.8413,
     "specialties": ["trauma", "fracture", "cardiac", "orthopedic"],
     "icu_beds_available": 50, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.6},

    # Delhi
    {"name": "AIIMS Delhi", "city": "New Delhi", "state": "Delhi",
     "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi - 110029",
     "phone": "011-26588500", "latitude": 28.5672, "longitude": 77.2100,
     "specialties": ["trauma", "cardiac", "neurology", "burn", "fracture", "head_injury"],
     "icu_beds_available": 120, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 6.0, "rating": 4.9},
    {"name": "Safdarjung Hospital", "city": "New Delhi", "state": "Delhi",
     "address": "Ring Road, New Delhi - 110029",
     "phone": "011-26165060", "latitude": 28.5687, "longitude": 77.2035,
     "specialties": ["trauma", "burn", "fracture", "bleeding"],
     "icu_beds_available": 90, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.5, "rating": 4.4},
    {"name": "Max Super Speciality Hospital Saket", "city": "New Delhi", "state": "Delhi",
     "address": "Press Enclave Road, Saket, New Delhi - 110017",
     "phone": "011-26515050", "latitude": 28.5274, "longitude": 77.2159,
     "specialties": ["cardiac", "neurology", "trauma", "orthopedic"],
     "icu_beds_available": 65, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 8.5, "rating": 4.7},
    {"name": "Fortis Escorts Heart Institute", "city": "New Delhi", "state": "Delhi",
     "address": "Okhla Road, New Delhi - 110025",
     "phone": "011-47135000", "latitude": 28.5497, "longitude": 77.2613,
     "specialties": ["cardiac", "stroke"],
     "icu_beds_available": 40, "trauma_center": False, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.8},

    # Bangalore
    {"name": "Manipal Hospital Bangalore", "city": "Bangalore", "state": "Karnataka",
     "address": "98, HAL Airport Road, Bengaluru - 560017",
     "phone": "080-25024444", "latitude": 12.9617, "longitude": 77.6412,
     "specialties": ["trauma", "cardiac", "neurology", "orthopedic"],
     "icu_beds_available": 70, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.6},
    {"name": "Narayana Health City", "city": "Bangalore", "state": "Karnataka",
     "address": "258/A, Bommasandra Industrial Area, Anekal Taluk",
     "phone": "080-71222222", "latitude": 12.8246, "longitude": 77.6748,
     "specialties": ["cardiac", "trauma", "neurology", "burn"],
     "icu_beds_available": 100, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.0, "rating": 4.7},
    {"name": "Apollo Hospital Bangalore", "city": "Bangalore", "state": "Karnataka",
     "address": "154/11, Opp. IIM-B, Bannerghatta Road, Bangalore - 560076",
     "phone": "080-26304050", "latitude": 12.8956, "longitude": 77.5984,
     "specialties": ["trauma", "cardiac", "fracture", "head_injury"],
     "icu_beds_available": 55, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 8.5, "rating": 4.5},

    # Chennai
    {"name": "Apollo Hospitals Chennai", "city": "Chennai", "state": "Tamil Nadu",
     "address": "21, Greams Lane, Off Greams Road, Chennai - 600006",
     "phone": "044-28296000", "latitude": 13.0635, "longitude": 80.2518,
     "specialties": ["trauma", "cardiac", "neurology", "burn", "orthopedic"],
     "icu_beds_available": 85, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.5, "rating": 4.8},
    {"name": "MIOT International", "city": "Chennai", "state": "Tamil Nadu",
     "address": "4/112, Mount Poonamallee Road, Manapakkam, Chennai - 600089",
     "phone": "044-22496789", "latitude": 13.0147, "longitude": 80.1741,
     "specialties": ["orthopedic", "fracture", "trauma", "cardiac"],
     "icu_beds_available": 40, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.5},
    {"name": "Government Royapettah Hospital", "city": "Chennai", "state": "Tamil Nadu",
     "address": "Royapettah High Road, Chennai - 600014",
     "phone": "044-28520781", "latitude": 13.0569, "longitude": 80.2622,
     "specialties": ["trauma", "burn", "bleeding", "fracture"],
     "icu_beds_available": 30, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.1},

    # Hyderabad
    {"name": "Yashoda Hospital Hyderabad", "city": "Hyderabad", "state": "Telangana",
     "address": "Raj Bhavan Road, Somajiguda, Hyderabad - 500082",
     "phone": "040-45674567", "latitude": 17.4238, "longitude": 78.4636,
     "specialties": ["cardiac", "neurology", "trauma", "stroke"],
     "icu_beds_available": 60, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.6},
    {"name": "Care Hospital Hyderabad", "city": "Hyderabad", "state": "Telangana",
     "address": "Exhibition Road, Nampally, Hyderabad - 500001",
     "phone": "040-30418000", "latitude": 17.3859, "longitude": 78.4742,
     "specialties": ["trauma", "burn", "cardiac", "fracture"],
     "icu_beds_available": 45, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 8.5, "rating": 4.4},

    # Pune
    {"name": "Ruby Hall Clinic", "city": "Pune", "state": "Maharashtra",
     "address": "40, Sassoon Road, Pune - 411001",
     "phone": "020-26163391", "latitude": 18.5314, "longitude": 73.8757,
     "specialties": ["trauma", "cardiac", "neurology", "burn"],
     "icu_beds_available": 50, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.5, "rating": 4.5},
    {"name": "Sahyadri Hospital Pune", "city": "Pune", "state": "Maharashtra",
     "address": "30-C, Karve Road, Erandwane, Pune - 411004",
     "phone": "020-67213700", "latitude": 18.5089, "longitude": 73.8398,
     "specialties": ["trauma", "fracture", "orthopedic", "cardiac"],
     "icu_beds_available": 35, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.4},

    # Kolkata
    {"name": "AMRI Hospital Kolkata", "city": "Kolkata", "state": "West Bengal",
     "address": "JC-16 & 17, Salt Lake City, Kolkata - 700098",
     "phone": "033-66800000", "latitude": 22.5727, "longitude": 88.4316,
     "specialties": ["trauma", "cardiac", "neurology"],
     "icu_beds_available": 40, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.4},
    {"name": "Medica Superspecialty Hospital", "city": "Kolkata", "state": "West Bengal",
     "address": "127, Mukundapur, EM Bypass, Kolkata - 700099",
     "phone": "033-40001111", "latitude": 22.5012, "longitude": 88.3989,
     "specialties": ["cardiac", "neurology", "trauma", "stroke"],
     "icu_beds_available": 55, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.5},

    # Ahmedabad
    {"name": "Apollo Hospital Ahmedabad", "city": "Ahmedabad", "state": "Gujarat",
     "address": "Plot No. 1A, GIDC Bhat, Gandhinagar - 382428",
     "phone": "079-66701800", "latitude": 23.1285, "longitude": 72.6428,
     "specialties": ["trauma", "cardiac", "fracture", "burn"],
     "icu_beds_available": 60, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.6},
    {"name": "Sterling Hospital Ahmedabad", "city": "Ahmedabad", "state": "Gujarat",
     "address": "Off Gurukul Road, Memnagar, Ahmedabad - 380052",
     "phone": "079-40011000", "latitude": 23.0552, "longitude": 72.5489,
     "specialties": ["trauma", "cardiac", "neurology"],
     "icu_beds_available": 35, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.5, "rating": 4.3},

    # Jaipur
    {"name": "Fortis Escorts Hospital Jaipur", "city": "Jaipur", "state": "Rajasthan",
     "address": "Jawaharlal Nehru Marg, Malviya Nagar, Jaipur - 302017",
     "phone": "0141-2547000", "latitude": 26.8449, "longitude": 75.8069,
     "specialties": ["cardiac", "trauma", "orthopedic", "fracture"],
     "icu_beds_available": 45, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.5, "rating": 4.5},
    {"name": "SMS Hospital Jaipur", "city": "Jaipur", "state": "Rajasthan",
     "address": "JLN Marg, Milap Nagar, Jaipur - 302004",
     "phone": "0141-2518888", "latitude": 26.8947, "longitude": 75.8021,
     "specialties": ["trauma", "burn", "fracture", "bleeding"],
     "icu_beds_available": 80, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.0, "rating": 4.2},

    # Chandigarh
    {"name": "PGI Chandigarh", "city": "Chandigarh", "state": "Punjab",
     "address": "Sector 12, Chandigarh - 160012",
     "phone": "0172-2756565", "latitude": 30.7647, "longitude": 76.7728,
     "specialties": ["trauma", "neurology", "cardiac", "burn", "head_injury"],
     "icu_beds_available": 100, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 6.5, "rating": 4.7},

    # Lucknow
    {"name": "KGMU Lucknow", "city": "Lucknow", "state": "Uttar Pradesh",
     "address": "Shah Mina Road, Chowk, Lucknow - 226003",
     "phone": "0522-2257540", "latitude": 26.8522, "longitude": 80.9423,
     "specialties": ["trauma", "neurology", "cardiac", "fracture"],
     "icu_beds_available": 90, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.0, "rating": 4.5},
    {"name": "Medanta The Medicity Lucknow", "city": "Lucknow", "state": "Uttar Pradesh",
     "address": "Sector A, Pocket 1, Amar Shaheed Path, Lucknow - 226030",
     "phone": "0522-4500000", "latitude": 26.7606, "longitude": 80.9858,
     "specialties": ["cardiac", "trauma", "neurology", "burn"],
     "icu_beds_available": 55, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.6},

    # Gurgaon
    {"name": "Medanta The Medicity Gurugram", "city": "Gurugram", "state": "Haryana",
     "address": "CH Baktawar Singh Road, Sector 38, Gurugram - 122001",
     "phone": "0124-4141414", "latitude": 28.4489, "longitude": 77.0434,
     "specialties": ["cardiac", "trauma", "neurology", "orthopedic", "burn"],
     "icu_beds_available": 110, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.0, "rating": 4.8},
    {"name": "Artemis Hospital Gurugram", "city": "Gurugram", "state": "Haryana",
     "address": "Sector 51, Gurugram - 122001",
     "phone": "0124-4511111", "latitude": 28.4247, "longitude": 77.0472,
     "specialties": ["trauma", "cardiac", "fracture", "neurology"],
     "icu_beds_available": 60, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 8.5, "rating": 4.5},

    # Noida
    {"name": "Fortis Hospital Noida", "city": "Noida", "state": "Uttar Pradesh",
     "address": "B-22, Sector 62, Noida - 201301",
     "phone": "0120-2400444", "latitude": 28.6271, "longitude": 77.3647,
     "specialties": ["trauma", "cardiac", "orthopedic", "fracture"],
     "icu_beds_available": 45, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.5, "rating": 4.4},

    # Nagpur
    {"name": "Alexis Hospital Nagpur", "city": "Nagpur", "state": "Maharashtra",
     "address": "50, Manish Nagar, Sonegaon, Nagpur - 440015",
     "phone": "0712-6600100", "latitude": 21.1228, "longitude": 79.0476,
     "specialties": ["trauma", "cardiac", "fracture"],
     "icu_beds_available": 30, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.3},

    # Surat
    {"name": "Kiran Multi Super Speciality Hospital Surat", "city": "Surat", "state": "Gujarat",
     "address": "Udhna - Magdalla Road, Surat - 395002",
     "phone": "0261-2559999", "latitude": 21.1702, "longitude": 72.8311,
     "specialties": ["trauma", "burn", "cardiac", "fracture"],
     "icu_beds_available": 40, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.3},

    # Indore
    {"name": "Bombay Hospital Indore", "city": "Indore", "state": "Madhya Pradesh",
     "address": "Ring Road, Indore - 452010",
     "phone": "0731-4077000", "latitude": 22.7196, "longitude": 75.8577,
     "specialties": ["trauma", "cardiac", "fracture", "burn"],
     "icu_beds_available": 35, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.3},

    # Coimbatore
    {"name": "PSG Hospitals Coimbatore", "city": "Coimbatore", "state": "Tamil Nadu",
     "address": "Peelamedu, Coimbatore - 641004",
     "phone": "0422-4345000", "latitude": 11.0168, "longitude": 77.0101,
     "specialties": ["cardiac", "trauma", "fracture", "neurology"],
     "icu_beds_available": 45, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.5, "rating": 4.4},

    # Kochi
    {"name": "Amrita Institute of Medical Sciences", "city": "Kochi", "state": "Kerala",
     "address": "AIMS Ponekkara P.O, Kochi - 682041",
     "phone": "0484-2801234", "latitude": 10.0124, "longitude": 76.3281,
     "specialties": ["trauma", "cardiac", "neurology", "burn", "fracture"],
     "icu_beds_available": 70, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.7},
    {"name": "Aster Medcity Kochi", "city": "Kochi", "state": "Kerala",
     "address": "Kuttisahib Road, South Chittoor, Kochi - 682027",
     "phone": "0484-6699999", "latitude": 9.9467, "longitude": 76.3278,
     "specialties": ["cardiac", "trauma", "orthopedic", "neurology"],
     "icu_beds_available": 50, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.5, "rating": 4.6},

    # Trivandrum
    {"name": "SCTIMST Trivandrum", "city": "Thiruvananthapuram", "state": "Kerala",
     "address": "Poojapura, Trivandrum - 695012",
     "phone": "0471-2524400", "latitude": 8.5241, "longitude": 76.9366,
     "specialties": ["cardiac", "neurology", "stroke"],
     "icu_beds_available": 40, "trauma_center": False, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.6},

    # Bhubaneswar
    {"name": "AIIMS Bhubaneswar", "city": "Bhubaneswar", "state": "Odisha",
     "address": "Sijua, Patrapada, Bhubaneswar - 751019",
     "phone": "0674-2476780", "latitude": 20.2012, "longitude": 85.8180,
     "specialties": ["trauma", "cardiac", "fracture", "neurology"],
     "icu_beds_available": 60, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.5},

    # Patna
    {"name": "PMCH Patna", "city": "Patna", "state": "Bihar",
     "address": "Ashok Raj Path, Patna - 800004",
     "phone": "0612-2300736", "latitude": 25.6177, "longitude": 85.1367,
     "specialties": ["trauma", "burn", "fracture", "bleeding"],
     "icu_beds_available": 50, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.1},

    # Guwahati
    {"name": "Gauhati Medical College Hospital", "city": "Guwahati", "state": "Assam",
     "address": "Bhangagarh, Guwahati - 781032",
     "phone": "0361-2529457", "latitude": 26.1736, "longitude": 91.7397,
     "specialties": ["trauma", "fracture", "burn", "cardiac"],
     "icu_beds_available": 45, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.1},

    # Dehradun
    {"name": "Doon Medical College Hospital", "city": "Dehradun", "state": "Uttarakhand",
     "address": "Haridwar Bypass Road, New Tehri, Dehradun - 248001",
     "phone": "0135-2652093", "latitude": 30.3165, "longitude": 78.0322,
     "specialties": ["trauma", "fracture", "cardiac"],
     "icu_beds_available": 30, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 11.0, "rating": 4.0},

    # Ranchi
    {"name": "Rajendra Institute of Medical Sciences", "city": "Ranchi", "state": "Jharkhand",
     "address": "Bariatu Road, Ranchi - 834009",
     "phone": "0651-2542500", "latitude": 23.3625, "longitude": 85.3290,
     "specialties": ["trauma", "burn", "fracture"],
     "icu_beds_available": 40, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.0},

    # Vadodara
    {"name": "SSG Hospital Vadodara", "city": "Vadodara", "state": "Gujarat",
     "address": "Sayajiganj, Vadodara - 390001",
     "phone": "0265-2225001", "latitude": 22.3119, "longitude": 73.1828,
     "specialties": ["trauma", "burn", "fracture", "bleeding", "cardiac"],
     "icu_beds_available": 55, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 8.5, "rating": 4.2},

    # Visakhapatnam
    {"name": "King George Hospital Visakhapatnam", "city": "Visakhapatnam", "state": "Andhra Pradesh",
     "address": "Maharani Peta, Visakhapatnam - 530002",
     "phone": "0891-2754724", "latitude": 17.7231, "longitude": 83.3012,
     "specialties": ["trauma", "burn", "fracture", "cardiac"],
     "icu_beds_available": 60, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.2},

    # Mysore
    {"name": "JSS Hospital Mysore", "city": "Mysuru", "state": "Karnataka",
     "address": "MG Road, Agrahara, Mysuru - 570004",
     "phone": "0821-2335000", "latitude": 12.3052, "longitude": 76.6551,
     "specialties": ["trauma", "cardiac", "fracture", "neurology"],
     "icu_beds_available": 40, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.5, "rating": 4.3},

    # Bhopal
    {"name": "AIIMS Bhopal", "city": "Bhopal", "state": "Madhya Pradesh",
     "address": "Saket Nagar, Bhopal - 462020",
     "phone": "0755-2672355", "latitude": 23.2547, "longitude": 77.4120,
     "specialties": ["trauma", "cardiac", "neurology", "burn", "fracture"],
     "icu_beds_available": 70, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.5, "rating": 4.5},

    # Agra
    {"name": "SN Medical College Agra", "city": "Agra", "state": "Uttar Pradesh",
     "address": "MG Road, Agra - 282002",
     "phone": "0562-2526505", "latitude": 27.1767, "longitude": 78.0081,
     "specialties": ["trauma", "burn", "fracture", "cardiac"],
     "icu_beds_available": 35, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 10.0, "rating": 4.0},

    # Varanasi
    {"name": "BHU Sir Sundar Lal Hospital", "city": "Varanasi", "state": "Uttar Pradesh",
     "address": "BHU Campus, Lanka, Varanasi - 221005",
     "phone": "0542-2368572", "latitude": 25.2677, "longitude": 82.9913,
     "specialties": ["trauma", "cardiac", "fracture", "burn"],
     "icu_beds_available": 50, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.0, "rating": 4.2},

    # Amritsar
    {"name": "Guru Nanak Dev Hospital Amritsar", "city": "Amritsar", "state": "Punjab",
     "address": "Circular Road, Amritsar - 143001",
     "phone": "0183-2256825", "latitude": 31.6340, "longitude": 74.8723,
     "specialties": ["trauma", "fracture", "burn", "cardiac"],
     "icu_beds_available": 40, "trauma_center": True, "helipad": False,
     "blood_bank": True, "avg_response_time_min": 9.5, "rating": 4.1},

    # Raipur
    {"name": "AIIMS Raipur", "city": "Raipur", "state": "Chhattisgarh",
     "address": "Tatibandh, GE Road, Raipur - 492099",
     "phone": "0771-2573764", "latitude": 21.2514, "longitude": 81.6296,
     "specialties": ["trauma", "cardiac", "fracture", "neurology"],
     "icu_beds_available": 55, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 8.0, "rating": 4.4},

    # Jodhpur
    {"name": "AIIMS Jodhpur", "city": "Jodhpur", "state": "Rajasthan",
     "address": "Basni Phase-II, Jodhpur - 342005",
     "phone": "0291-2740741", "latitude": 26.2389, "longitude": 73.0243,
     "specialties": ["trauma", "cardiac", "fracture", "burn"],
     "icu_beds_available": 60, "trauma_center": True, "helipad": True,
     "blood_bank": True, "avg_response_time_min": 7.5, "rating": 4.4},
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select
        result = await session.execute(select(Hospital).limit(1))
        if result.scalar_one_or_none():
            print("✅ Hospitals already seeded.")
            return

        for h in HOSPITALS:
            hospital = Hospital(**h)
            session.add(hospital)

        await session.commit()
        print(f"✅ Seeded {len(HOSPITALS)} hospitals.")


if __name__ == "__main__":
    asyncio.run(seed())
