"""Pydantic models for LinkedIn Profile data parsing."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class ProfileResponse(BaseModel):
    success: bool = True
    profile: Optional["ParsedProfile"] = None


class ProfileLocation(BaseModel):
    country: str = ""
    city: str = ""
    country_code: str = ""


class ExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    start_date: str = ""
    end_date: str = ""


class EducationItem(BaseModel):
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""


class ProjectItem(BaseModel):
    title: str = ""
    description: str = ""


class PublicationItem(BaseModel):
    name: str = ""
    description: str = ""
    publisher: str = ""
    url: str = ""
    published_date: str = ""
    authors: List[Dict[str, str]] = []


class ProfileImage(BaseModel):
    url: str = ""
    width: Optional[int] = None
    height: Optional[int] = None


class ParsedProfile(BaseModel):
    name: str = ""
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    industry: str = ""
    about: str = ""
    location: ProfileLocation = ProfileLocation()
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    skills: List[str] = []
    certifications: List[str] = []
    projects: List[ProjectItem] = []
    publications: List[PublicationItem] = []
    languages: List[str] = []
    profile_images: List[ProfileImage] = []
    public_identifier: str = ""
    entity_urn: str = ""  


class ProfileRequest(BaseModel):
    profile_url: str = Field(..., description="LinkedIn profile URL (For E.g. https://www.linkedin.com/in/varunkumawat/)")
          