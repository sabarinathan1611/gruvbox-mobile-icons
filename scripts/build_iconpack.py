"""Generate the Android icon-pack Gradle project in iconpack/ (Nova / Lawnchair / ADW format).

Reads icons/png/*.png and mapping/components.txt; writes everything under iconpack/ except
the Gradle wrapper. Safe to re-run: generated resources are replaced each time.

Usage:  .venv/Scripts/python.exe scripts/build_iconpack.py
Then:   cd iconpack && gradlew.bat assembleDebug
"""
import os
import shutil
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from apps import APPS, FALLBACK, owner_of

ROOT = Path(__file__).resolve().parent.parent
PNG_DIR = ROOT / "icons" / "png"
COMPONENTS = ROOT / "mapping" / "components.txt"
PROJECT = ROOT / "iconpack"
APP = PROJECT / "app"
MAIN = APP / "src" / "main"
RES = MAIN / "res"

PACKAGE = "com.sabari.gruvboxclean"
AGP_VERSION = "9.5.0"
COMPILE_SDK = 36
MIN_SDK = 26
VERSION_CODE = 2
VERSION_NAME = "0.2.0"
ICONBACK_SCALE = "0.62"  # how large an unthemed app's own icon sits on the tile

SDK_DIR = Path(os.environ.get("ANDROID_HOME") or
               Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk")

# ---------- static project files ----------

SETTINGS = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "GruvboxClean"
include(":app")
"""

ROOT_BUILD = f"""plugins {{
    id("com.android.application") version "{AGP_VERSION}" apply false
}}
"""

GRADLE_PROPERTIES = """org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
"""

APP_BUILD = f"""plugins {{
    id("com.android.application")
}}

// CI sets these; local builds fall back to the defaults below and the debug key
val keystoreFile: String? = System.getenv("ICONPACK_KEYSTORE")

android {{
    namespace = "{PACKAGE}"
    compileSdk = {COMPILE_SDK}

    defaultConfig {{
        applicationId = "{PACKAGE}"
        minSdk = {MIN_SDK}
        targetSdk = {COMPILE_SDK}
        versionCode = System.getenv("ICONPACK_VERSION_CODE")?.toInt() ?: {VERSION_CODE}
        versionName = System.getenv("ICONPACK_VERSION_NAME") ?: "{VERSION_NAME}"
    }}

    signingConfigs {{
        if (keystoreFile != null) {{
            create("release") {{
                storeFile = file(keystoreFile)
                storePassword = System.getenv("ICONPACK_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("ICONPACK_KEY_ALIAS")
                keyPassword = System.getenv("ICONPACK_KEY_PASSWORD")
            }}
        }}
    }}

    buildTypes {{
        release {{
            // Icons are looked up by name from XML, so the shrinker must not touch resources
            isMinifyEnabled = false
            isShrinkResources = false
            signingConfig = signingConfigs.getByName(if (keystoreFile != null) "release" else "debug")
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
}}
"""

GITIGNORE = """.gradle/
build/
app/build/
local.properties
*.iml
.idea/
"""

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <application
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:theme="@android:style/Theme.Material.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>

            <!-- Icon-pack discovery: Nova, Lawnchair, ADW, Apex, Atom, Go and friends -->
            <intent-filter>
                <action android:name="org.adw.launcher.THEMES" />
                <action android:name="org.adw.launcher.icons.ACTION_PICK_ICON" />
                <action android:name="com.novalauncher.THEME" />
                <action android:name="com.teslacoilsw.launcher.THEME" />
                <action android:name="com.dlto.atom.launcher.THEME" />
                <action android:name="com.gau.go.launcherex.theme" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="com.anddoes.launcher.THEME" />
                <category android:name="com.fede.launcher.THEME_ICONPACK" />
                <category android:name="com.teslacoilsw.launcher.THEME" />
                <category android:name="android.intent.category.DEFAULT" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

MAIN_ACTIVITY = f"""package {PACKAGE};

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Insets;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.text.Editable;
import android.text.InputType;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.inputmethod.EditorInfo;
import android.widget.AbsListView;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Searchable grid of every icon in the pack. When a launcher opens it with
 * ACTION_PICK_ICON, tapping an icon returns it to the launcher.
 */
public class MainActivity extends Activity {{
    private static final String ACTION_PICK_ICON = "org.adw.launcher.icons.ACTION_PICK_ICON";
    private static final int FG = 0xFFEBDBB2;
    private static final int GRAY = 0xFF928374;
    private static final int BG0 = 0xFF282828;
    private static final int BG1 = 0xFF3C3836;

    private final List<Integer> icons = new ArrayList<>();
    private final List<String> labels = new ArrayList<>();
    private final List<String> keys = new ArrayList<>();
    private final List<Integer> shown = new ArrayList<>();
    private BaseAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        boolean picking = ACTION_PICK_ICON.equals(getIntent().getAction());

        String[] names = getResources().getStringArray(R.array.icon_pack);
        String[] titles = getResources().getStringArray(R.array.icon_labels);
        for (int i = 0; i < names.length; i++) {{
            int id = getResources().getIdentifier(names[i], "drawable", getPackageName());
            if (id == 0) continue;
            String title = i < titles.length ? titles[i] : names[i];
            icons.add(id);
            labels.add(title);
            keys.add((title + " " + names[i]).toLowerCase(Locale.ROOT));
        }}

        float dp = getResources().getDisplayMetrics().density;
        int size = Math.round(56 * dp);
        int cellW = Math.round(76 * dp);
        int pad = Math.round(16 * dp);

        EditText search = new EditText(this);
        search.setHint(R.string.search_hint);
        search.setSingleLine(true);
        search.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        search.setImeOptions(EditorInfo.IME_ACTION_SEARCH);
        search.setTextColor(FG);
        search.setHintTextColor(GRAY);
        GradientDrawable field = new GradientDrawable();
        field.setColor(BG1);
        field.setCornerRadius(14 * dp);
        search.setBackground(field);
        search.setPadding(pad, Math.round(12 * dp), pad, Math.round(12 * dp));
        search.addTextChangedListener(new TextWatcher() {{
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {{ }}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {{ }}
            @Override public void afterTextChanged(Editable s) {{ filter(s.toString()); }}
        }});

        GridView grid = new GridView(this);
        grid.setNumColumns(GridView.AUTO_FIT);
        grid.setColumnWidth(cellW);
        grid.setStretchMode(GridView.STRETCH_SPACING_UNIFORM);
        grid.setVerticalSpacing(pad);
        grid.setClipToPadding(false);
        grid.setPadding(0, pad, 0, pad);
        adapter = new BaseAdapter() {{
            @Override public int getCount() {{ return shown.size(); }}
            @Override public Object getItem(int i) {{ return icons.get(shown.get(i)); }}
            @Override public long getItemId(int i) {{ return icons.get(shown.get(i)); }}
            @Override public View getView(int i, View convert, ViewGroup parent) {{
                LinearLayout cell;
                ImageView iv;
                TextView tv;
                if (convert instanceof LinearLayout) {{
                    cell = (LinearLayout) convert;
                    iv = (ImageView) cell.getChildAt(0);
                    tv = (TextView) cell.getChildAt(1);
                }} else {{
                    cell = new LinearLayout(MainActivity.this);
                    cell.setOrientation(LinearLayout.VERTICAL);
                    cell.setGravity(Gravity.CENTER_HORIZONTAL);
                    cell.setLayoutParams(new AbsListView.LayoutParams(cellW, ViewGroup.LayoutParams.WRAP_CONTENT));
                    iv = new ImageView(MainActivity.this);
                    cell.addView(iv, new LinearLayout.LayoutParams(size, size));
                    tv = new TextView(MainActivity.this);
                    tv.setTextColor(FG);
                    tv.setTextSize(11);
                    tv.setSingleLine(true);
                    tv.setEllipsize(TextUtils.TruncateAt.END);
                    tv.setGravity(Gravity.CENTER_HORIZONTAL);
                    tv.setPadding(0, Math.round(6 * dp), 0, 0);
                    cell.addView(tv, new LinearLayout.LayoutParams(cellW, ViewGroup.LayoutParams.WRAP_CONTENT));
                }}
                int k = shown.get(i);
                iv.setImageResource(icons.get(k));
                tv.setText(labels.get(k));
                return cell;
            }}
        }};
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, position, id) -> {{
            int res = icons.get(shown.get(position));
            if (picking) {{
                Bitmap bmp = BitmapFactory.decodeResource(getResources(), res);
                Intent result = new Intent();
                result.putExtra("icon", bmp);
                result.putExtra(Intent.EXTRA_SHORTCUT_ICON_RESOURCE,
                        Intent.ShortcutIconResource.fromContext(this, res));
                setResult(RESULT_OK, result);
                finish();
            }} else {{
                Toast.makeText(this, R.string.how_to_apply, Toast.LENGTH_LONG).show();
            }}
        }});

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG0);
        root.setPadding(pad, pad, pad, 0);
        root.addView(search, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(grid, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {{
            root.setOnApplyWindowInsetsListener((v, insets) -> {{
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                v.setPadding(pad + bars.left, pad + bars.top, pad + bars.right, bars.bottom);
                return insets;
            }});
        }}
        filter("");
        setContentView(root);
    }}

    private void filter(String query) {{
        String q = query.trim().toLowerCase(Locale.ROOT);
        shown.clear();
        for (int i = 0; i < icons.size(); i++) {{
            if (q.isEmpty() || keys.get(i).contains(q)) shown.add(i);
        }}
        adapter.notifyDataSetChanged();
    }}
}}
"""

STRINGS = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Gruvbox Clean</string>
    <string name="theme_title">Gruvbox Clean</string>
    <string name="theme_description">Flat Gruvbox icons with an orange accent.</string>
    <string name="theme_author">Sabari</string>
    <string name="search_hint">Search icons</string>
    <string name="how_to_apply">Apply this icon pack from your launcher settings (Lawnchair: Settings, Icon style; Nova: Look and feel, Icon style).</string>
</resources>
"""

# ---------- generated resources ----------


def read_components() -> list[tuple[str, str]]:
    rows = []
    for line in COMPONENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        component = line.split()[0]
        # Resolve against apps.py now, so edits there apply without re-querying the phone
        if drawable := owner_of(component):
            rows.append((component, drawable))
    # Exact components named in glyph files count even if no phone has reported them yet
    known = {c for c, _ in rows}
    for drawable, (_, targets) in APPS.items():
        rows += [(t, drawable) for t in targets if "/" in t and t not in known]
    return rows


def appfilter(rows) -> str:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>",
             "    <!-- Unthemed apps: their own icon, scaled onto the Gruvbox tile -->",
             '    <iconback img1="iconback" />',
             f'    <scale factor="{ICONBACK_SCALE}" />', ""]
    current = None
    for component, drawable in sorted(rows, key=lambda r: (r[1], r[0])):
        if drawable != current:
            lines.append(f"    <!-- {APPS[drawable][0]} -->")
            current = drawable
        comp = quoteattr(f"ComponentInfo{{{component}}}")
        lines.append(f'    <item component={comp} drawable="{drawable}" />')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def drawable_xml(names) -> str:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>", "    <version>1</version>",
             '    <category title="Apps" />']
    lines += [f'    <item drawable="{n}" />' for n in names]
    lines += ['    <category title="Extras" />', f'    <item drawable="{FALLBACK}" />',
              "</resources>"]
    return "\n".join(lines) + "\n"


def iconpack_xml(names) -> str:
    """ADW icon list plus a parallel array of labels for the in-app search."""
    items = "\n".join(f"        <item>{n}</item>" for n in [*names, FALLBACK])
    labels = "\n".join(f"        <item>{xml_text(APPS[n][0])}</item>" for n in names)
    return ('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            '    <string-array name="icon_pack" translatable="false">\n'
            f"{items}\n    </string-array>\n"
            '    <string-array name="icon_labels" translatable="false">\n'
            f"{labels}\n        <item>Fallback</item>\n    </string-array>\n</resources>\n")


def xml_text(s: str) -> str:
    """Escape for an Android string resource (XML entities plus quote and apostrophe)."""
    return escape(s).replace("'", "\\'").replace('"', '\\"')


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    names = sorted(APPS)
    missing = [n for n in [*names, FALLBACK, "iconback"] if not (PNG_DIR / f"{n}.png").exists()]
    if missing:
        raise SystemExit(f"render icons first (make_icons.py); missing: {', '.join(missing)}")
    rows = read_components()

    write(PROJECT / "settings.gradle.kts", SETTINGS)
    write(PROJECT / "build.gradle.kts", ROOT_BUILD)
    write(PROJECT / "gradle.properties", GRADLE_PROPERTIES)
    write(PROJECT / ".gitignore", GITIGNORE)
    write(PROJECT / "local.properties", f"sdk.dir={SDK_DIR.as_posix()}\n")
    write(APP / "build.gradle.kts", APP_BUILD)
    write(MAIN / "AndroidManifest.xml", MANIFEST)
    write(MAIN / "java" / Path(*PACKAGE.split(".")) / "MainActivity.java", MAIN_ACTIVITY)
    write(RES / "values" / "strings.xml", STRINGS)

    drawables = RES / "drawable-nodpi"
    shutil.rmtree(drawables, ignore_errors=True)
    drawables.mkdir(parents=True)
    for n in [*names, FALLBACK, "iconback"]:
        shutil.copy2(PNG_DIR / f"{n}.png", drawables / f"{n}.png")
    shutil.copy2(PNG_DIR / f"{FALLBACK}.png", drawables / "ic_launcher.png")

    filt = appfilter(rows)
    write(RES / "xml" / "appfilter.xml", filt)
    write(MAIN / "assets" / "appfilter.xml", filt)  # some launchers read assets/ instead
    write(RES / "xml" / "drawable.xml", drawable_xml(names))
    write(MAIN / "assets" / "drawable.xml", drawable_xml(names))
    write(RES / "values" / "iconpack.xml", iconpack_xml(names))

    print(f"generated {PROJECT}: {len(names) + 1} icons, {len(rows)} appfilter entries")


if __name__ == "__main__":
    main()
