"""Typed schema for ticket classification.

We use Pydantic + Gemini structured output (`response_schema` + `response_mime_type=
"application/json"`). The model is constrained to this schema, so the response comes
back as a validated `TicketClassification` object via `response.parsed` — using only
the allowed enum values. No regex, no "please return JSON", no retry-on-broken-JSON.
"""

from enum import Enum
from pydantic import BaseModel, Field


class Category(str, Enum):
    bug = "bug"
    feature_request = "feature_request"
    how_to = "how_to"


class Priority(str, Enum):
    low = "low"        # cosmetic / nice-to-have, no workflow impact
    medium = "medium"  # feature partially broken, workaround exists
    high = "high"      # core feature broken, no easy workaround
    urgent = "urgent"  # site down / data loss / payments broken / blocking launch


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    frustrated = "frustrated"
    angry = "angry"


class Plugin(str, Enum):
    """Primary Crocoblock / Jet plugin the ticket is about."""
    jetengine = "JetEngine"
    jetformbuilder = "JetFormBuilder"
    jetsmartfilters = "JetSmartFilters"
    jetelements = "JetElements"
    jetbooking = "JetBooking"
    jetappointment = "JetAppointment"
    jetreviews = "JetReviews"
    jetpopup = "JetPopup"
    jetmenu = "JetMenu"
    jettabs = "JetTabs"
    jetwoobuilder = "JetWooBuilder"
    jetsearch = "JetSearch"
    jetblog = "JetBlog"
    jetblocks = "JetBlocks"
    jetthemecore = "JetThemeCore"
    jetgridbuilder = "JetGridBuilder"
    jetproductgallery = "JetProductGallery"
    jetcomparewishlist = "JetCompareWishlist"
    other = "other"        # a Crocoblock product not in the list above
    unknown = "unknown"    # cannot tell which plugin from the ticket text


class TicketClassification(BaseModel):
    """Structured result the classifier must return for every ticket."""
    category: Category = Field(description="Type of request")
    priority: Priority = Field(description="Business urgency, see enum comments")
    plugin: Plugin = Field(description="Primary Jet/Crocoblock plugin involved")
    sentiment: Sentiment = Field(description="Emotional tone of the customer")
    confidence: float = Field(
        description="Model confidence in this classification, a number from 0 to 1"
    )
    reasoning: str = Field(
        description="One short sentence justifying the classification"
    )
