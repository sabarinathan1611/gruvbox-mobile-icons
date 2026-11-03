package com.sabari.gruvboxclean;

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
public class MainActivity extends Activity {
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
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean picking = ACTION_PICK_ICON.equals(getIntent().getAction());

        String[] names = getResources().getStringArray(R.array.icon_pack);
        String[] titles = getResources().getStringArray(R.array.icon_labels);
        for (int i = 0; i < names.length; i++) {
            int id = getResources().getIdentifier(names[i], "drawable", getPackageName());
            if (id == 0) continue;
            String title = i < titles.length ? titles[i] : names[i];
            icons.add(id);
            labels.add(title);
            keys.add((title + " " + names[i]).toLowerCase(Locale.ROOT));
        }

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
        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) { }
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) { }
            @Override public void afterTextChanged(Editable s) { filter(s.toString()); }
        });

        GridView grid = new GridView(this);
        grid.setNumColumns(GridView.AUTO_FIT);
        grid.setColumnWidth(cellW);
        grid.setStretchMode(GridView.STRETCH_SPACING_UNIFORM);
        grid.setVerticalSpacing(pad);
        grid.setClipToPadding(false);
        grid.setPadding(0, pad, 0, pad);
        adapter = new BaseAdapter() {
            @Override public int getCount() { return shown.size(); }
            @Override public Object getItem(int i) { return icons.get(shown.get(i)); }
            @Override public long getItemId(int i) { return icons.get(shown.get(i)); }
            @Override public View getView(int i, View convert, ViewGroup parent) {
                LinearLayout cell;
                ImageView iv;
                TextView tv;
                if (convert instanceof LinearLayout) {
                    cell = (LinearLayout) convert;
                    iv = (ImageView) cell.getChildAt(0);
                    tv = (TextView) cell.getChildAt(1);
                } else {
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
                }
                int k = shown.get(i);
                iv.setImageResource(icons.get(k));
                tv.setText(labels.get(k));
                return cell;
            }
        };
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, position, id) -> {
            int res = icons.get(shown.get(position));
            if (picking) {
                Bitmap bmp = BitmapFactory.decodeResource(getResources(), res);
                Intent result = new Intent();
                result.putExtra("icon", bmp);
                result.putExtra(Intent.EXTRA_SHORTCUT_ICON_RESOURCE,
                        Intent.ShortcutIconResource.fromContext(this, res));
                setResult(RESULT_OK, result);
                finish();
            } else {
                Toast.makeText(this, R.string.how_to_apply, Toast.LENGTH_LONG).show();
            }
        });

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG0);
        root.setPadding(pad, pad, pad, 0);
        root.addView(search, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(grid, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            root.setOnApplyWindowInsetsListener((v, insets) -> {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                v.setPadding(pad + bars.left, pad + bars.top, pad + bars.right, bars.bottom);
                return insets;
            });
        }
        filter("");
        setContentView(root);
    }

    private void filter(String query) {
        String q = query.trim().toLowerCase(Locale.ROOT);
        shown.clear();
        for (int i = 0; i < icons.size(); i++) {
            if (q.isEmpty() || keys.get(i).contains(q)) shown.add(i);
        }
        adapter.notifyDataSetChanged();
    }
}
