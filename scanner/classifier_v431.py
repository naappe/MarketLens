import re

TOP_ORDER = [
    "Electronics","Vehicles","Property","Home & Living","Baby & Kids",
    "Fashion","Health & Beauty","Sports & Outdoors","Business Equipment",
    "Services","Jobs","Other"
]

def norm(value):
    return " " + re.sub(r"\s+", " ", (value or "").lower()).strip() + " "

def contains_any(text, words):
    return any(w in text for w in words)

# Source categories are evidence, but not all source names are equally specific.
# trust=3: specific/authoritative source
# trust=1: broad source where a strong title can override
SOURCE_RULES = [
    ("Baby & Kids","Baby Gear",3,[
        "strollers & walkers","stroller","walkers","baby gear","pushchairs","pushchair"
    ]),
    ("Baby & Kids","Nursery",3,[
        "nursery decor","nursery","baby furniture","cots & cribs","cribs","bassinets"
    ]),
    ("Baby & Kids","Toys & School",3,[
        "toys & games","toys","school supplies","kids toys"
    ]),

    ("Electronics","Phones",3,[
        "mobile phones","mobile phone","phones & tablets","phones","smartphones","tablets"
    ]),
    ("Electronics","Computers",3,[
        "computers","laptops","computer accessories","printers"
    ]),
    ("Electronics","Cameras",3,["cameras","camera"]),
    ("Electronics","Gaming",3,["gaming","video games","consoles"]),
    ("Electronics","TV & Audio",3,["tv & audio","televisions","audio"]),

    ("Vehicles","Cars",3,["vehicles > cars","cars","car sales"]),
    ("Vehicles","Motorcycles",3,["motorcycles","motorbikes","scooters"]),
    ("Vehicles","Marine",3,["marine","boats","outboards"]),
    ("Vehicles","Parts",3,["vehicle parts","auto parts","car parts"]),
    ("Vehicles","General",3,["vehicles"]),

    ("Property","Apartments & Rooms",3,[
        "apartments","rooms","property rentals","rentals"
    ]),
    ("Property","Land & Houses",3,[
        "land & houses","houses","land","real estate","property"
    ]),

    ("Fashion","Clothing & Shoes",3,["clothing","shoes","fashion"]),
    ("Fashion","Accessories",3,["fashion accessories","bags & wallets"]),

    ("Health & Beauty","Beauty",3,["health & beauty","beauty","cosmetics","perfumes"]),
    ("Sports & Outdoors","Sports",3,["sports","fitness","outdoor"]),
    ("Business Equipment","Equipment",3,["business equipment","office equipment","industrial"]),
    ("Services","Services",3,["services"]),
    ("Jobs","Jobs",3,["jobs","vacancies","careers"]),

    # Broad home sources: strong title evidence may override these.
    ("Home & Living","Furniture",1,[
        "furniture & bedding","furniture","bedding"
    ]),
    ("Home & Living","Appliances",2,[
        "home appliances","appliances","kitchen appliances"
    ]),
    ("Home & Living","Kitchen & Tools",2,[
        "kitchen","tools","hardware"
    ]),
    ("Home & Living","General",1,["home & living","home"])
]

# Strong product-title signals. These are intentionally specific.
TITLE_RULES = [
    ("Baby & Kids","Baby Gear",[
        " stroller "," pushchair "," playpen "," play pen "," baby walker ",
        " baby carrier "," high chair "," rocking chair "," baby swing "
    ]),
    ("Baby & Kids","Nursery",[
        " baby bed "," baby cot "," crib "," bassinet "," baby mattress ",
        " nursery "," learning tower "," montessori "," kids bed "," kid bed "
    ]),
    ("Baby & Kids","Toys & School",[
        " kids toy "," kid toy "," baby toy "," school bag "," school supplies "
    ]),

    ("Electronics","Phones",[
        " iphone "," smartphone "," mobile phone "," galaxy s"," galaxy a",
        " galaxy z"," google pixel "," oneplus "," redmi "," poco "," ipad ",
        " tablet "
    ]),
    ("Electronics","Computers",[
        " laptop "," macbook "," desktop pc "," computer "," monitor ",
        " keyboard "," mouse "," printer "
    ]),
    ("Electronics","TV & Audio",[
        " television "," smart tv "," oled tv "," qled tv "," soundbar ",
        " speaker "," headphones "," earbuds "," airpods "
    ]),
    ("Electronics","Cameras",[
        " camera "," canon eos "," nikon "," gopro "," action camera "
    ]),
    ("Electronics","Gaming",[
        " playstation "," ps5 "," ps4 "," xbox "," nintendo switch "," gaming pc "
    ]),

    ("Vehicles","Cars",[
        " toyota "," honda fit "," nissan "," suzuki swift "," mitsubishi ",
        " hyundai "," kia "," mazda "," car for sale "
    ]),
    ("Vehicles","Motorcycles",[
        " motorcycle "," motorbike "," scooter "," yamaha nmax "," vespa "
    ]),
    ("Vehicles","Marine",[
        " outboard "," speedboat "," dinghy "," marine engine "
    ]),

    ("Property","Apartments & Rooms",[
        " apartment for rent "," room for rent "," flat for rent "," studio apartment "
    ]),
    ("Property","Land & Houses",[
        " house for rent "," house for sale "," land for sale "
    ]),

    ("Home & Living","Appliances",[
        " air conditioner "," aircon "," refrigerator "," fridge "," washing machine ",
        " microwave "," cooker "," freezer "," water dispenser "
    ]),
    ("Home & Living","Furniture",[
        " sofa "," dining table "," wardrobe "," cabinet "," office chair "
    ]),
    ("Home & Living","Kitchen & Tools",[
        " power drill "," grinder "," kitchen set "," cookware "
    ]),

    ("Fashion","Clothing & Shoes",[
        " t-shirt "," tshirt "," shirt "," dress "," abaya "," sneakers "," shoes "
    ]),
    ("Fashion","Accessories",[
        " handbag "," wallet "," sunglasses "
    ]),
    ("Health & Beauty","Beauty",[
        " perfume "," makeup "," skincare "," cosmetic "
    ]),
    ("Sports & Outdoors","Sports",[
        " treadmill "," dumbbell "," football "," gym equipment "," bicycle "
    ]),
    ("Services","Services",[
        " repair service "," installation service "," cleaning service "
    ]),
    ("Jobs","Jobs",[
        " vacancy "," hiring "," job opening "," recruitment "
    ])
]

def source_match(source_category):
    s=norm(source_category)
    best=None
    for top,sub,trust,words in SOURCE_RULES:
        if contains_any(s, words):
            score=max(len(w) for w in words if w in s)
            candidate=(top,sub,trust,score)
            if best is None or (trust,score) > (best[2],best[3]):
                best=candidate
    return best

def title_match(title):
    t=norm(title)

    # Portable AC often appears simply as "AC 12000btu".
    if "btu" in t and (" ac " in t or " a/c " in t):
        return ("Home & Living","Appliances",3)

    best=None
    for top,sub,words in TITLE_RULES:
        hits=[w for w in words if w in t]
        if hits:
            score=max(len(w) for w in hits)
            candidate=(top,sub,3,score)
            if best is None or score > best[3]:
                best=candidate
    return best

def classify(title, source_category="", listing_type=""):
    intent="Wanted" if (listing_type or "").lower()=="wanted" else "For Sale"
    sm=source_match(source_category)
    tm=title_match(title)

    # A trusted specific source wins against incidental wording.
    if sm and sm[2] >= 3:
        top,sub=sm[0],sm[1]
        confidence=97 if (not tm or tm[0]==top) else 90
        reason="specific source" if not tm else (
            "source + title agree" if tm[0]==top else "specific source overrides title"
        )
        return top,sub,intent,confidence,reason

    # A strong product title can override broad sources such as Furniture & Bedding.
    if tm:
        top,sub=tm[0],tm[1]
        if sm and sm[0]==top:
            return top,sub,intent,95,"title + broad source agree"
        if sm and sm[0]!=top:
            return top,sub,intent,90,"strong title overrides broad source"
        return top,sub,intent,88,"strong title"

    if sm:
        return sm[0],sm[1],intent,78,"broad source"

    return "Other","Other",intent,30,"insufficient evidence"
