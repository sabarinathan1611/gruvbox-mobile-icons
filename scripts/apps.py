"""App catalogue: which drawable (and glyph) each package gets.

Each entry: drawable name -> (label, [packages]).
The drawable name is also the glyph name in glyphs.py and the file name in icons/svg|png.
To theme a new app: add a glyph in glyphs.py, add an entry here, re-run the scripts.
"""

APPS: dict[str, tuple[str, list[str]]] = {
    # browsers & search
    "fennec": ("Fennec", ["org.mozilla.fennec_fdroid"]),
    "brave": ("Brave", ["com.brave.browser"]),
    "duckduckgo": ("DuckDuckGo", ["com.duckduckgo.mobile.android"]),
    "browser": ("Browser", ["com.vivo.browser", "com.iqoo.website"]),
    # app stores
    "aurora": ("Aurora Store", ["com.aurora.store"]),
    "fdroid": ("F-Droid", ["org.fdroid.fdroid"]),
    "obtainium": ("Obtainium", ["dev.imranr.obtainium.fdroid"]),
    "playstore": ("Play Store", ["com.android.vending"]),
    # messaging
    "whatsapp": ("WhatsApp", ["com.whatsapp"]),
    "telegram": ("Telegram", ["org.telegram.messenger"]),
    "forkgram": ("Forkgram", ["org.forkgram.classic"]),
    "signal": ("Signal", ["org.thoughtcrime.securesms"]),
    "messages": ("Messages", ["org.fossify.messages", "com.android.mms"]),
    # mail
    "protonmail": ("Proton Mail", ["ch.protonmail.android"]),
    "tuta": ("Tuta", ["de.tutao.tutanota"]),
    "thunderbird": ("Thunderbird", ["net.thunderbird.android"]),
    "gmail": ("Gmail", ["com.google.android.gm"]),
    # social & video
    "reddit": ("Reddit", ["com.reddit.frontpage"]),
    "tiktok": ("TikTok", ["com.zhiliaoapp.musically"]),
    "newpipe": ("NewPipe", ["org.schabi.newpipe"]),
    "vlc": ("VLC", ["org.videolan.vlc", "com.android.VideoPlayer"]),
    "netflix": ("Netflix", ["com.netflix.mediaclient"]),
    "hotstar": ("Hotstar", ["in.startv.hotstar"]),
    "jellyfin": ("Jellyfin", ["org.jellyfin.mobile"]),
    "letterboxd": ("Letterboxd", ["com.letterboxd.letterboxd"]),
    "mihon": ("Mihon", ["app.mihon"]),
    # music
    "spotify": ("Spotify", ["com.spotify.music"]),
    "simpmusic": ("SimpMusic", ["com.maxrave.simpmusic"]),
    "spotube": ("Spotube", ["oss.krtirtho.spotube"]),
    # games, dev, fitness
    "steam": ("Steam", ["com.valvesoftware.android.steam.community"]),
    "github": ("GitHub", ["com.github.android"]),
    "strava": ("Strava", ["com.strava"]),
    # money
    "paytm": ("Paytm", ["net.one97.paytm"]),
    "gpay": ("Google Pay", ["com.google.android.apps.nbu.paisa.user"]),
    "canarabank": ("Canara Bank", ["com.canarabank.mobility"]),
    # shopping, food, services
    "amazon": ("Amazon", ["in.amazon.mShop.android.shopping"]),
    "swiggy": ("Swiggy", ["in.swiggy.android"]),
    "zepto": ("Zepto", ["com.zeptoconsumerapp"]),
    "district": ("District", ["com.application.zomato.district"]),
    "myjio": ("MyJio", ["com.jio.myjio"]),
    "whereismytrain": ("Where Is My Train", ["com.whereismytrain.android"]),
    # privacy & network
    "protonvpn": ("Proton VPN", ["ch.protonvpn.android"]),
    "nextdns": ("NextDNS Manager", ["com.doubleangels.nextdnsmanagement"]),
    "privatedns": ("Private DNS Toggle", ["ru.karasevm.privatednstoggle"]),
    "ntfy": ("ntfy", ["io.heckel.ntfy"]),
    "aegis": ("Aegis", ["com.beemdevelopment.aegis"]),
    "msauth": ("MS Auth", ["com.azure.authenticator"]),
    "gauth": ("Google Auth", ["com.google.android.apps.authenticator2"]),
    # torrents
    "qbitcontroller": ("qBit Controller", ["dev.bartuzen.qbitcontroller"]),
    "libretorrent": ("LibreTorrent", ["org.proninyaroslav.libretorrent"]),
    # files & photos
    "gallery": ("Gallery", ["org.fossify.gallery", "com.vivo.gallery"]),
    "calendar": ("Calendar", ["org.fossify.calendar"]),
    "gcalendar": ("Google Calendar", ["com.google.android.calendar"]),
    "filemanager": ("File Manager", ["org.fossify.filemanager"]),
    "files": ("Files", ["com.android.filemanager"]),
    "voyager": ("Voyager", ["com.voyagerfiles"]),
    "ente": ("Ente Photos", ["io.ente.photos.independent"]),
    "snapseed": ("Snapseed", ["com.niksoftware.snapseed"]),
    # input & tools
    "leantype": ("LeanType", ["com.leanbitlab.leantype"]),
    "simplekeyboard": ("Simple Keyboard", ["rkr.simplekeyboard.inputmethod"]),
    "codescanner": ("Code Scanner", ["com.secuso.privacyFriendlyCodeScanner"]),
    # system
    "phone": ("Phone", ["com.android.contacts/com.android.dialer.TwelveKeyDialer"]),
    "contacts": ("Contacts", ["com.android.contacts/com.android.contacts.DialtactsContactsEntryActivity"]),
    "camera": ("Camera", ["com.android.camera"]),
    "settings": ("Settings", ["com.android.settings"]),
    "clock": ("Clock", ["com.android.deskclock"]),
    "calculator": ("Calculator", ["com.vivo.calculator"]),
    "maps": ("Maps", ["com.google.android.apps.maps"]),
    # vivo / iQOO system apps
    "weather": ("Weather", ["com.vivo.weather"]),
    "themes": ("Themes", ["com.bbk.theme"]),
    "vappstore": ("V-AppStore", ["com.vivo.appstore"]),
    "recorder": ("Recorder", ["com.vivo.soundrecorder"]),
    "simpleview": ("Simple View", ["com.vivo.simplelauncher"]),
    "notes": ("Notes", ["com.vivo.notes"]),
    "iqoocloud": ("iQOO Cloud", ["com.bbk.cloud"]),
    "compass": ("Compass", ["com.vivo.compass"]),
    "easyshare": ("EasyShare", ["com.vivo.easyshare"]),
    "gamecenter": ("Game Center", ["com.vivo.game"]),
    "imanager": ("i Manager", ["com.vivo.imanager"]),
    # extras
    "bountyrush": ("Bounty Rush", ["com.bandainamcoent.opbrww"]),
    "gold": ("Gold", ["com.joyalukkas.mcstaging.twa"]),
    "angelone": ("Angel One", ["com.msf.angelmobile"]),
    "cassettecat": ("CassetteCat", ["in.caffeinelabs.cassettecat"]),
}

# Shown for any app without a custom icon (also the generic "default" drawable)
FALLBACK = "fallback"


def owner_of(component: str) -> str | None:
    """Return the drawable for a full 'pkg/pkg.Activity' component, or None.

    An entry can name a whole package or one exact component (needed when one package,
    like com.android.contacts, exposes two launcher icons).
    """
    pkg = component.split("/", 1)[0]
    for drawable, (_, targets) in APPS.items():
        if component in targets:
            return drawable
    for drawable, (_, targets) in APPS.items():
        if pkg in targets:
            return drawable
    return None
