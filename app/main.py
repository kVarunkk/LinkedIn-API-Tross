from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, Optional
import logging
from .config import settings
from .linkedin_client import LinkedInClient
from .models import ProfileResponse, ParsedProfile, ProfileLocation, ProfileRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LinkedIn Profile API",
    description="Accepts a LinkedIn profile URL and returns structured JSON.",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client() -> LinkedInClient:
    """Build a LinkedIn client from environment variables."""
    li_at = settings.LINKEDIN_LI_AT
    jsessionid = settings.LINKEDIN_JSESSIONID
    if not li_at or not jsessionid:
        raise HTTPException(
            status_code=500,
            detail="Set LINKEDIN_LI_AT and LINKEDIN_JSESSIONID env vars.",
        )
    return LinkedInClient(li_at, jsessionid, settings.USER_AGENT)


def extract_vanity(profile_url: str) -> str:
    """Pull the vanity name from a LinkedIn URL or return the input as-is."""
    if "/" in profile_url:
        return profile_url.rstrip("/").split("/")[-1]
    return profile_url

def parse_profile(raw: Dict[str, Any], vanity: str) -> ParsedProfile:
    """Translate the LinkedIn REST response into the assignment's schema."""
    profile = raw.get("elements", [{}])[0] if raw.get("elements") else raw

    first = profile.get("firstName", "")
    last = profile.get("lastName", "")
    name = f"{first} {last}".strip() or vanity

    location = profile.get("location", {}) or {}
    geo = (profile.get("geoLocation", {}) or {}).get("geo", {}) or {}
    country = (geo.get("country", {}) or {}).get("defaultLocalizedName") or location.get("countryCode", "")
    city = geo.get("defaultLocalizedNameWithoutCountryName", "")

    industry = (profile.get("industry", {}) or {}).get("name", "")

    # Multi-locale name strings -> English values
    def en(d, key="en_US"):
        if not d:
            return ""
        if isinstance(d, dict) and key in d:
            return d[key]
        return ""

    experience = []
    for group in (profile.get("profilePositionGroups", {}) or {}).get("elements", []):
        for pos in (group.get("profilePositionInPositionGroup", {}) or {}).get("elements", []):
            dr = pos.get("dateRange", {}) or {}
            start = dr.get("start", {}) or {}
            end = dr.get("end", {}) or {}
            experience.append({
                "title": en(pos.get("multiLocaleTitle")),
                "company": en(pos.get("multiLocaleCompanyName")),
                "location": en(pos.get("multiLocaleLocationName")),
                "description": en(pos.get("multiLocaleDescription")),
                "start_date": f"{start.get('year', '')}-{str(start.get('month', '')).zfill(2)}",
                "end_date": f"{end.get('year', '')}-{str(end.get('month', '')).zfill(2)}" if end else "Present",
            })

    education = []
    for edu in (profile.get("profileEducations", {}) or {}).get("elements", []):
        dr = edu.get("dateRange", {}) or {}
        start = dr.get("start", {}) or {}
        end = dr.get("end", {}) or {}
        education.append({
            "degree": en(edu.get("multiLocaleDegreeName")) or edu.get("degreeName", ""),
            "institution": en(edu.get("multiLocaleSchoolName")) or edu.get("schoolName", ""),
            "start_date": f"{start.get('year', '')}-{str(start.get('month', '')).zfill(2)}",
            "end_date": f"{end.get('year', '')}-{str(end.get('month', '')).zfill(2)}" if end else "Present",
        })

    projects = []
    for project in (profile.get("profileProjects", {}) or {}).get("elements", []):
        title = project.get("title", "No Project title")
        description = project.get("description", "No Project description")
        projects.append({
            "title": title,
            "description": description
        })    

    skills = [en(s.get("multiLocaleName")) for s in (profile.get("profileSkills", {}) or {}).get("elements", [])]
    skills = [s for s in skills if s]

    certifications = [en(c.get("multiLocaleName")) for c in (profile.get("profileCertifications", {}) or {}).get("elements", [])]
    certifications = [c for c in certifications if c]

    languages = [en(l.get("multiLocaleName")) for l in (profile.get("profileLanguages", {}) or {}).get("elements", [])]
    languages = [l for l in languages if l]

    # Publications
    publications = []
    for pub in (profile.get("profilePublications", {}) or {}).get("elements", []):
        pub_on = pub.get("publishedOn", {}) or {}
        pub_date = None
        if pub_on:
            pub_date = f"{pub_on.get('year', '')}-{str(pub_on.get('month', '')).zfill(2)}-{str(pub_on.get('day', '')).zfill(2)}"
        publications.append({
            "name": en(pub.get("multiLocaleName")) or pub.get("name", ""),
            "description": en(pub.get("multiLocaleDescription")) or pub.get("description", ""),
            "publisher": en(pub.get("multiLocalePublisher")) or pub.get("publisher", ""),
            "url": pub.get("url", ""),
            "published_date": pub_date,
            "authors": [{
                "name": (a.get("standardizedContributor", {}) or {}).get("lastName", "")
            } for a in pub.get("authors", []) if a],
        })

    # Build profile image URLs from the artifacts on the picture deco spec
    images = []
    for pic_key in ("profilePicture", "backgroundPicture"):
        pic = profile.get(pic_key) or {}
        vi = (pic.get("displayImageReference", {}) or {}).get("vectorImage", {}) or {}
        root = vi.get("rootUrl", "")
        for art in vi.get("artifacts", []) or []:
            seg = art.get("fileIdentifyingUrlPathSegment", "")
            if root and seg:
                images.append({
                    "url": f"{root}{seg}",
                    "width": art.get("width"),
                    "height": art.get("height"),
                })

    return ParsedProfile(
       name=name,
       first_name=first,
       last_name=last,
       headline=en(profile.get("multiLocaleHeadline")) or profile.get("headline", ""),
       industry=industry,
       about=en(profile.get("multiLocaleSummary")) or profile.get("summary", ""),
       location= ProfileLocation(country=country, city=city, country_code=location.get("countryCode", "")),
       experience=experience,
       education=education,
       skills=skills,
       certifications=certifications,
       projects=projects,
       publications=publications,
       languages=languages,
       profile_images=images,
       public_identifier=profile.get("publicIdentifier", vanity),
       entity_urn=profile.get("entityUrn", ""),
   )            


@app.get("/")
async def root():
    return {
        "message": "LinkedIn Profile API",
        "endpoints": {
            "POST /profile": "Get profile (body: profile_url)",
            "GET /health": "Health check",
        },
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy" if settings.LINKEDIN_LI_AT and settings.LINKEDIN_JSESSIONID else "missing_credentials",
        "credentials_configured": bool(settings.LINKEDIN_LI_AT and settings.LINKEDIN_JSESSIONID),
    }


@app.post("/profile", response_model=ProfileResponse)
async def get_profile(
    request: ProfileRequest,
    x_li_at: Optional[str] = Header(None, alias="X-Li-At"),
    x_jsessionid: Optional[str] = Header(None, alias="X-JSessionID"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
    x_li_track: Optional[str] = Header(None, alias="X-Li-Track"),
):
    vanity = extract_vanity(request.profile_url)
    li_at = x_li_at or settings.LINKEDIN_LI_AT
    jsessionid = x_jsessionid or settings.LINKEDIN_JSESSIONID
    ua = user_agent or settings.USER_AGENT
    track = x_li_track  # pass raw JSON string
    if not li_at or not jsessionid:
        raise HTTPException(
            status_code=400,
            detail="Provide session cookies via X-Li-At and X-JSessionID headers (or set LINKEDIN_LI_AT / LINKEDIN_JSESSIONID env vars).",
        )
    client = LinkedInClient(li_at, jsessionid, ua, track)
    try:
        raw = await client.get_full_profile(vanity)
        parsed = parse_profile(raw, vanity)
        return {"success": True, "profile": parsed}
    except Exception as e:
        logger.error(f"Profile fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"LinkedIn API error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
