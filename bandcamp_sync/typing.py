from __future__ import annotations

from typing import TypedDict


class BandcampWishlistItem(TypedDict):
    fan_id: int
    item_id: int
    item_type: str
    band_id: int
    added: str
    updated: str
    purchased: None
    sale_item_id: None
    sale_item_type: None
    tralbum_id: int
    tralbum_type: str
    featured_track: int
    why: None
    hidden: None
    index: None
    also_collected_count: int
    url_hints: UrlHints
    item_title: str
    item_url: str
    item_art_id: int
    item_art_url: str
    item_art: ItemArt
    band_name: str
    band_url: str
    genre_id: int
    featured_track_title: str
    featured_track_number: int
    featured_track_is_custom: bool
    featured_track_duration: float
    featured_track_url: None
    featured_track_encodings_id: int
    package_details: None
    num_streamable_tracks: int
    is_purchasable: bool
    is_private: bool
    is_preorder: bool
    is_giftable: bool
    is_subscriber_only: bool
    is_subscription_item: bool
    service_name: None
    service_url_fragment: None
    gift_sender_name: None
    gift_sender_note: None
    gift_id: None
    gift_recipient_name: None
    album_id: int
    album_title: str
    listen_in_app_url: None
    band_location: None
    band_image_id: None
    release_count: None
    message_count: None
    is_set_price: bool
    price: float
    has_digital_download: None
    merch_ids: None
    merch_sold_out: None
    currency: str
    label: None
    label_id: None
    require_email: None
    item_art_ids: None
    releases: None
    discount: None
    token: str
    variant_id: None
    merch_snapshot: None
    featured_track_license_id: None
    licensed_item: None
    download_available: bool


class UrlHints(TypedDict):
    subdomain: str
    custom_domain: None
    custom_domain_verified: None
    slug: str
    item_type: str


class ItemArt(TypedDict):
    url: str
    thumb_url: str
    art_id: int


from typing import Any, NotRequired, Union

from typing_extensions import TypedDict

File = TypedDict("File", {"mp3-128": str})

class TrackinfoJson(TypedDict):
    id: int
    track_id: int
    file: File
    artist: None
    title: str
    encodings_id: int
    license_type: int
    private: None
    track_num: int
    album_preorder: bool
    unreleased_track: bool
    title_link: str
    has_lyrics: bool
    has_info: bool
    streaming: int
    is_downloadable: bool
    has_free_download: None
    free_album_download: bool
    duration: float
    lyrics: None
    sizeof_lyrics: int
    is_draft: bool
    video_source_type: None
    video_source_id: None
    video_mobile_url: None
    video_poster_url: None
    video_id: None
    video_caption: None
    video_featured: None
    alt_link: None
    encoding_error: None
    encoding_pending: None
    play_count: None
    is_capped: None
    track_license_id: None

class PlayCapData(TypedDict):
    streaming_limits_enabled: bool
    streaming_limit: int

class Current(TypedDict):
    audit: int
    title: str
    new_date: str
    mod_date: str
    publish_date: str
    private: None
    killed: None
    download_pref: int
    require_email: None
    is_set_price: None
    set_price: float
    minimum_price: float
    minimum_price_nonzero: float
    require_email_0: None
    artist: str
    about: str
    credits: str
    auto_repriced: None
    new_desc_format: int
    band_id: int
    selling_band_id: int
    art_id: int
    download_desc_id: None
    release_date: str
    upc: None
    purchase_url: None
    purchase_title: None
    featured_track_id: int
    id: int
    type: str

Sponsor = TypedDict(
    "Sponsor",
    {
        "@type": str,
        "url": str,
        "image": str,
        "additionalProperty": list["AdditionalProperty"],
        "name": NotRequired[str],
    },
)

Item = TypedDict(
    "Item",
    {
        "@type": str,
        "@id": str,
        "additionalProperty": list["AdditionalProperty"],
        "name": str,
        "duration": str,
        "copyrightNotice": str,
        "mainEntityOfPage": str,
    },
)

ItemListElement = TypedDict(
    "ItemListElement", {"@type": str, "position": int, "item": Item}
)

Track = TypedDict(
    "Track",
    {"@type": str, "numberOfItems": int, "itemListElement": list[ItemListElement]},
)

SubjectOf = TypedDict(
    "SubjectOf",
    {
        "@type": str,
        "url": str,
        "name": str,
        "additionalProperty": list["AdditionalProperty"],
    },
)

MainEntityOfPage = TypedDict(
    "MainEntityOfPage", {"@type": str, "url": str, "name": str}
)

Publisher = TypedDict(
    "Publisher",
    {
        "@type": str,
        "@id": str,
        "name": str,
        "additionalProperty": list["AdditionalProperty"],
        "image": str,
        "genre": str,
        "description": str,
        "mainEntityOfPage": list[MainEntityOfPage],
        "subjectOf": list[SubjectOf],
    },
)

ByArtist = TypedDict("ByArtist", {"@type": str, "name": str})

class PriceSpecification(TypedDict):
    minPrice: float

Offers = TypedDict(
    "Offers",
    {
        "@type": str,
        "url": str,
        "priceCurrency": str,
        "price": float,
        "priceSpecification": PriceSpecification,
        "availability": str,
    },
)

UnnammedUnion45E0B0 = Union[bool, str, int]

AdditionalProperty = TypedDict(
    "AdditionalProperty", {"@type": str, "name": str, "value": UnnammedUnion45E0B0}
)

UnnammedUnion45DDA0 = Union[str, list[str]]

AlbumRelease = TypedDict(
    "AlbumRelease",
    {
        "@type": UnnammedUnion45DDA0,
        "@id": str,
        "name": NotRequired[str],
        "additionalProperty": NotRequired[list[AdditionalProperty]],
        "description": NotRequired[str],
        "offers": NotRequired[Offers],
        "musicReleaseFormat": NotRequired[str],
        "image": NotRequired[list[str]],
    },
)

class RecFooter(TypedDict):
    pass

class Identities(TypedDict):
    user: None
    ip_country_code: str
    fan: None
    is_page_band_member: None
    subscribed_to_page_band: None
    bands: list[Any]
    partner: bool
    is_admin: None
    labels: list[Any]
    page_band: None
    active_licenses: list[Any]

class a618540384(TypedDict):
    id: int
    name: str
    currency: str
    max_price: float
    digital_vat_enabled: bool
    is_dsa_trader: bool

ItemSellers = TypedDict("ItemSellers", {"618540384": a618540384})

class FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld(TypedDict):
    name: str
    value: str
    norm_name: str

Subgenres = TypedDict(
    "Subgenres",
    {
        "acoustic": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "alternative": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "ambient": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "blues": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "classical": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "comedy": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "country": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "devotional": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "electronic": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "experimental": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "folk": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "funk": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "hip-hop-rap": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "jazz": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "kids": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "latin": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "metal": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "pop": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "punk": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "r-b-soul": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "reggae": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "rock": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "soundtrack": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "spoken-word": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
        "world": list[
            FunkOrCountryOrAcousticOrAmbientOrSpokenWordOrJazzOrClassicalOrPunkOrRBSoulOrBlueOrAlternativeOrReggaeOrExperimentalOrMetalOrPopOrComedyOrElectronicOrLatinOrHipHopRapOrDevotionalOrFolkOrSoundtrackOrKidOrRockOrWorld
        ],
    },
)

class Genre(TypedDict):
    id: int
    name: str
    norm_name: str
    value: str

class MailingListInfo(TypedDict):
    email_address: None

class SignupParams(TypedDict):
    save_card: bool
    mailing_list_info: MailingListInfo
    genres: list[Genre]
    subgenres: Subgenres
    activation_url: str
    activation_sig: str
    is_phone: bool
    isMobile: bool

class BuyerLocation(TypedDict):
    country_code: str
    is_eu: bool

class LiveEventTickets(TypedDict):
    pass

class Cfg(TypedDict):
    mobile_app: bool
    gifting: bool
    physical_gifting: bool
    physical_gifting_zip_regex: bool
    tralbum_login: bool
    no_flash_uploads: bool
    artist_subscriptions: bool
    video_sharing: bool
    open_signup: bool
    stream_buffer_duration_stats: bool
    fan_page_2017: bool
    header_rework_2018: bool
    band_navbar_update_2023: bool
    dsa_buy_dialog: bool
    single_sign_up: bool
    fan_signup_use_captcha: bool
    login_use_captcha: bool
    mobile_onboarding: bool
    gift_cards: bool
    menubar_autocomplete_enabled: bool
    use_elasticsearch_backed_search: bool
    new_search_api_service: bool
    search_tracking: bool
    order_history: bool
    search_discovery_one_filter_desktop_only: bool
    search_discovery_one_filter_rollout: bool
    community: bool

class EmbedInfo(TypedDict):
    public_embeddable: bool
    exclusive_embeddable: bool
    item_public: bool
    no_track_preorder: bool

class SidebarDisco(TypedDict):
    music_grid: bool
    discography_real_size: int
    sidebar_max_size: int
    sidebar_collapse_size: int

class Languages(TypedDict):
    en: str
    de: str
    es: str
    fr: str
    pt: str
    ja: str

class Templglobals(TypedDict):
    endpoint_mobilized: bool
    is_phone: bool

BandcampPageInfo = TypedDict(
    "UnnammedType45EBA0",
    {
        "recaptcha_public_key": str,
        "invisible_recaptcha_public_key": str,
        "templglobals": Templglobals,
        "localize_page": bool,
        "locale": str,
        "languages": Languages,
        "help_center_url": str,
        "env": str,
        "sidebar_disco": SidebarDisco,
        "user_territory": None,
        "tralbum_is_promo": None,
        "embed_info": EmbedInfo,
        "fan_follows_label": None,
        "login_bounce_url": str,
        "cfg": Cfg,
        "media_mode_test": bool,
        "lo_querystr": str,
        "ip_location_country_code": str,
        "fan_location_country": None,
        "show_buy_full_disco": None,
        "live_event_tickets": LiveEventTickets,
        "buyer_location": BuyerLocation,
        "signup_params": SignupParams,
        "mobile_app_url": str,
        "platform_app_url": None,
        "app_store_url": str,
        "play_store_url": str,
        "unsupported_device": bool,
        "fan_tralbum_data": None,
        "album_id": int,
        "pgload_sample_rate": int,
        "item_sellers": ItemSellers,
        "gift_card_balance": None,
        "limited_checkout": bool,
        "ab_test_tralbum_auth_entrypoints": bool,
        "identities": Identities,
        "rec_footer": RecFooter,
        "show_tos_banner_layout": bool,
        "albumReleaseType": str,
        "@id": str,
        "mainEntityOfPage": str,
        "@type": str,
        "name": str,
        "dateModified": str,
        "albumRelease": list[AlbumRelease],
        "byArtist": ByArtist,
        "publisher": Publisher,
        "numTracks": int,
        "track": Track,
        "image": str,
        "keywords": list[str],
        "datePublished": str,
        "description": str,
        "creditText": str,
        "copyrightNotice": str,
        "sponsor": list[Sponsor],
        "additionalProperty": list[AdditionalProperty],
        "@context": str,
        "for the curious": str,
        "current": Current,
        "preorder_count": None,
        "hasAudio": bool,
        "art_id": int,
        "packages": None,
        "defaultPrice": float,
        "freeDownloadPage": None,
        "FREE": int,
        "PAID": int,
        "artist": str,
        "item_type": str,
        "id": int,
        "last_subscription_item": None,
        "has_discounts": bool,
        "is_bonus": None,
        "play_cap_data": PlayCapData,
        "is_purchased": None,
        "items_purchased": None,
        "is_private_stream": None,
        "is_band_member": None,
        "licensed_version_ids": None,
        "package_associated_license_id": None,
        "has_video": None,
        "tralbum_subscriber_only": bool,
        "featured_track_id": int,
        "initial_track_num": None,
        "is_preorder": bool,
        "album_is_preorder": bool,
        "album_release_date": str,
        "trackinfo": list[TrackinfoJson],
        "playing_from": str,
        "url": str,
        "use_expando_lyrics": bool,
    },
)

# 💡 Starting from Python 3.10 (PEP 604), `Union[A, B]` can be simplified as `A | B`

# 💡 `NotRequired` or `Missing` are introduced since Python 3.11 (PEP 655).
#   `typing_extensions` is imported above for backwards compatibility.
#   For Python < 3.11, pip install typing_extensions. O.W., just change it to `typing`\n
