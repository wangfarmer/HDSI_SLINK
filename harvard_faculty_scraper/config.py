from __future__ import annotations

import json
from pathlib import Path

from .models import SchoolConfig


DEFAULT_SCHOOL_CONFIGS: dict[str, SchoolConfig] = {
    "harvard_college_dso_staff": SchoolConfig(
        key="harvard_college_dso_staff",
        name="Harvard College Dean of Students Office Staff",
        seed_urls=["https://dso.college.harvard.edu/people/people-type/staff"],
        allowed_domains=["dso.college.harvard.edu"],
        profile_link_patterns=[r"/people/"],
        exclude_link_patterns=[r"#", r"/people/people-type/staff$"],
        profile_required_patterns=[r"/people/[^/]+/?$"],
        list_page_patterns=[r"/people/people-type/staff\?page=\d+$"],
    ),
    "harvard_gsas_staff": SchoolConfig(
        key="harvard_gsas_staff",
        name="Harvard Kenneth C. Griffin Graduate School of Arts and Sciences Staff",
        seed_urls=["https://gsas.harvard.edu/directory/staff"],
        allowed_domains=["gsas.harvard.edu"],
        profile_link_patterns=[r"/person/"],
        exclude_link_patterns=[r"#", r"/directory/staff$"],
        profile_required_patterns=[r"/person/[^/]+/?$"],
        list_page_patterns=[r"/directory/staff\?page=\d+$"],
    ),
    "harvard_seas": SchoolConfig(
        key="harvard_seas",
        name="Harvard John A. Paulson School of Engineering and Applied Sciences",
        seed_urls=["https://seas.harvard.edu/about-us/directory"],
        allowed_domains=["seas.harvard.edu"],
        profile_link_patterns=[r"/person/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[r"/person/[^/]+/?$"],
        list_page_patterns=[r"/about-us/directory\?page=%2C\d+$"],
    ),
    "harvard_extension_school": SchoolConfig(
        key="harvard_extension_school",
        name="Harvard Extension School",
        seed_urls=["https://extension.harvard.edu/faculty/"],
        allowed_domains=["extension.harvard.edu"],
        profile_link_patterns=[r"/faculty/"],
        exclude_link_patterns=[r"#", r"/faculty/$"],
        profile_required_patterns=[r"/faculty/[^/]+/?$"],
        list_page_patterns=[r"/faculty/page/\d+/?$"],
    ),
    "harvard_kennedy_school": SchoolConfig(
        key="harvard_kennedy_school",
        name="Harvard Kennedy School",
        seed_urls=["https://www.hks.harvard.edu/faculty-profiles"],
        allowed_domains=["www.hks.harvard.edu", "hks.harvard.edu"],
        profile_link_patterns=[r"/faculty/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[r"/faculty/[A-Za-z0-9][A-Za-z0-9-]*/?$"],
        list_page_patterns=[r"/faculty-profiles\?page=\d+$"],
    ),
    "harvard_business_school": SchoolConfig(
        key="harvard_business_school",
        name="Harvard Business School",
        seed_urls=["https://pubwww.hbs.edu/faculty/Pages/browse.aspx"],
        allowed_domains=["www.hbs.edu", "hbs.edu", "pubwww.hbs.edu"],
        profile_link_patterns=[r"/faculty/Pages/profile\.aspx", r"/faculty/Pages/item\.aspx"],
        exclude_link_patterns=[r"#", r"/faculty/Pages/browse\.aspx", r"/faculty/Pages/default\.aspx"],
        profile_required_patterns=[r"/faculty/Pages/profile\.aspx", r"/faculty/Pages/item\.aspx"],
    ),
    "harvard_law_school": SchoolConfig(
        key="harvard_law_school",
        name="Harvard Law School",
        seed_urls=["https://hls.harvard.edu/faculty/?page=1"],
        allowed_domains=["hls.harvard.edu"],
        profile_link_patterns=[r"/faculty/"],
        exclude_link_patterns=[r"/faculty/$", r"#"],
        profile_required_patterns=[r"/faculty/[A-Za-z0-9][A-Za-z0-9-]*/?$"],
        list_page_patterns=[
            r"/faculty/\?(?:type=hls_faculty&)?page=\d+(?:&type=hls_faculty)?$",
            r"/faculty/page/\d+/?$",
        ],
    ),
    "harvard_graduate_school_of_design": SchoolConfig(
        key="harvard_graduate_school_of_design",
        name="Harvard Graduate School of Design",
        seed_urls=[
            "https://www.gsd.harvard.edu/people/faculty/",
            "https://www.gsd.harvard.edu/people/staff/",
            "https://www.gsd.harvard.edu/people/affiliate/",
        ],
        api_seed_urls=[
            "https://www.gsd.harvard.edu/wp-json/gsd/v1/people?type=faculty&per_page=48&page=1",
            "https://www.gsd.harvard.edu/wp-json/gsd/v1/people?type=staff&per_page=48&page=1",
            "https://www.gsd.harvard.edu/wp-json/gsd/v1/people?type=affiliate&per_page=48&page=1",
        ],
        allowed_domains=["www.gsd.harvard.edu", "gsd.harvard.edu"],
        profile_link_patterns=[r"/person/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[r"/person/[^/]+/?$"],
    ),
    "harvard_medical_school": SchoolConfig(
        key="harvard_medical_school",
        name="Harvard Medical School - DBMI People",
        seed_urls=["https://dbmi.hms.harvard.edu/people"],
        allowed_domains=["dbmi.hms.harvard.edu"],
        profile_link_patterns=[r"/people/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[r"/people/[A-Za-z0-9][A-Za-z0-9-]*/?$"],
    ),
    "harvard_t_h_chan_school_public_health": SchoolConfig(
        key="harvard_t_h_chan_school_public_health",
        name="Harvard T.H. Chan School of Public Health",
        seed_urls=["https://hsph.harvard.edu/profiles/"],
        api_seed_urls=["https://hsph.harvard.edu/wp-json/wp/v2/faculty_profiles?per_page=100&page=1&parent=0"],
        allowed_domains=["www.hsph.harvard.edu", "hsph.harvard.edu"],
        profile_link_patterns=[r"/profile/", r"/faculty/"],
        exclude_link_patterns=[r"#", r"/faculty/$"],
        profile_required_patterns=[r"/profile/[^/]+/?$", r"/faculty/[^/]+/?$"],
    ),
    "harvard_divinity_school": SchoolConfig(
        key="harvard_divinity_school",
        name="Harvard Divinity School",
        seed_urls=["https://hds.harvard.edu/people"],
        allowed_domains=["hds.harvard.edu"],
        profile_link_patterns=[r"/people/"],
        exclude_link_patterns=[r"#", r"/people$"],
        profile_required_patterns=[r"/people/[^/]+/?$"],
    ),
    "harvard_education_school": SchoolConfig(
        key="harvard_education_school",
        name="Harvard Graduate School of Education",
        seed_urls=[
            "https://www.gse.harvard.edu/directory/faculty",
            "https://www.gse.harvard.edu/directory/staff",
            "https://www.gse.harvard.edu/directory/phd-students",
            "https://www.gse.harvard.edu/directory/edld-students",
        ],
        allowed_domains=["www.gse.harvard.edu", "gse.harvard.edu"],
        profile_link_patterns=[r"/directory/(faculty|staff|phd-students|edld-students)/"],
        exclude_link_patterns=[
            r"#",
            r"/directory/faculty$",
            r"/directory/staff$",
            r"/directory/phd-students$",
            r"/directory/edld-students$",
        ],
        profile_required_patterns=[r"/directory/(faculty|staff|phd-students|edld-students)/[^/]+/?$"],
    ),
    "harvard_school_of_dental_medicine": SchoolConfig(
        key="harvard_school_of_dental_medicine",
        name="Harvard School of Dental Medicine",
        seed_urls=["https://www.hsdm.harvard.edu/hsdm-directory"],
        allowed_domains=["www.hsdm.harvard.edu", "hsdm.harvard.edu"],
        profile_link_patterns=[r"/people/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[r"/people/[^/]+/?$"],
        list_page_patterns=[r"/hsdm-directory\?page=\d+$"],
    ),
    "harvard_radcliffe_institute": SchoolConfig(
        key="harvard_radcliffe_institute",
        name="Harvard Radcliffe Institute",
        seed_urls=[
            "https://www.radcliffe.harvard.edu/radcliffe-fellowship/fellows",
            "https://www.radcliffe.harvard.edu/about-the-institute/faculty-directors",
        ],
        allowed_domains=["www.radcliffe.harvard.edu", "radcliffe.harvard.edu"],
        profile_link_patterns=[r"/people/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[r"/people/[^/?#]+(?:\?listing=\d+)?$"],
        list_page_patterns=[r"/radcliffe-fellowship/fellows\?page=\d+$"],
    ),
    "harvard_wyss_institute": SchoolConfig(
        key="harvard_wyss_institute",
        name="Harvard Wyss Institute",
        seed_urls=[
            "https://wyss.harvard.edu/team/core-faculty/",
            "https://wyss.harvard.edu/team/associate-faculty/",
            "https://wyss.harvard.edu/team/clinical-fellows/",
            "https://wyss.harvard.edu/team/postdoctoral-fellow/",
            "https://wyss.harvard.edu/team/technology-development-fellows/",
            "https://wyss.harvard.edu/team/visiting-scholars/",
            "https://wyss.harvard.edu/team/strategic-engagement/",
            "https://wyss.harvard.edu/team/business-development-team/",
            "https://wyss.harvard.edu/team/advanced-technology-team/",
            "https://wyss.harvard.edu/team/research-support/",
            "https://wyss.harvard.edu/team/biosafety-and-lab-safety/",
            "https://wyss.harvard.edu/team/clinical-research-team/",
            "https://wyss.harvard.edu/team/veterinary-team/",
            "https://wyss.harvard.edu/team/administration-operations/",
        ],
        allowed_domains=["wyss.harvard.edu"],
        profile_link_patterns=[r"/team/"],
        exclude_link_patterns=[r"#"],
        profile_required_patterns=[
            r"/team/(?:core-faculty|associate-faculty|clinical-fellows|postdoctoral-fellow|technology-development-fellows|visiting-scholars|strategic-engagement|business-development-team|advanced-technology-team|research-support|biosafety-and-lab-safety|clinical-research-team|veterinary-team|administration-operations)/[^/]+/?$"
        ],
    ),
}


def get_school_config(key: str) -> SchoolConfig:
    try:
        return DEFAULT_SCHOOL_CONFIGS[key]
    except KeyError as exc:
        available = ", ".join(sorted(DEFAULT_SCHOOL_CONFIGS))
        raise KeyError(f"Unknown school '{key}'. Available schools: {available}") from exc


def load_school_config(path: Path) -> SchoolConfig:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return SchoolConfig(
        key=payload["key"],
        name=payload["name"],
        seed_urls=list(payload["seed_urls"]),
        allowed_domains=list(payload["allowed_domains"]),
        profile_link_patterns=list(payload.get("profile_link_patterns", [])),
        exclude_link_patterns=list(payload.get("exclude_link_patterns", [])),
        profile_required_patterns=list(payload.get("profile_required_patterns", [])),
        list_page_patterns=list(payload.get("list_page_patterns", [])),
        api_seed_urls=list(payload.get("api_seed_urls", [])),
    )
