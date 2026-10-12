package pl.rizz.client;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;

public final class Gfx {
    public static final int ACCENT = 0xFFFF375F;

    public static void rrect(DrawContext c, int x, int y, int w, int h, int r, int color) {
        r = Math.max(0, Math.min(r, Math.min(w, h) / 2));
        if (r == 0) { c.fill(x, y, x + w, y + h, color); return; }
        c.fill(x + r, y, x + w - r, y + h, color);
        c.fill(x, y + r, x + r, y + h - r, color);
        c.fill(x + w - r, y + r, x + w, y + h - r, color);
        for (int i = 0; i < r; i++) {
            double dy = r - i - 0.5;
            int inset = r - (int) Math.floor(Math.sqrt(r * r - dy * dy));
            c.fill(x + inset, y + i, x + r, y + i + 1, color);
            c.fill(x + w - r, y + i, x + w - inset, y + i + 1, color);
            c.fill(x + inset, y + h - 1 - i, x + r, y + h - i, color);
            c.fill(x + w - r, y + h - 1 - i, x + w - inset, y + h - i, color);
        }
    }

    public static void text(DrawContext c, String s, int x, int y, int color) {
        c.drawText(MinecraftClient.getInstance().textRenderer, s, x, y, color, false);
    }

    public static void textShadow(DrawContext c, String s, int x, int y, int color) {
        c.drawText(MinecraftClient.getInstance().textRenderer, s, x, y, color, true);
    }

    public static int width(String s) {
        return MinecraftClient.getInstance().textRenderer.getWidth(s);
    }

    public static void centered(DrawContext c, String s, int cx, int y, int color) {
        text(c, s, cx - width(s) / 2, y, color);
    }

    public static void toggle(DrawContext c, int x, int y, boolean on) {
        rrect(c, x, y, 28, 16, 8, on ? ACCENT : 0xFF55555F);
        rrect(c, on ? x + 14 : x + 2, y + 2, 12, 12, 6, 0xFFFFFFFF);
    }

    /** Logo Rizz Client: zaokraglony kwadrat z litera R. */
    public static void logo(DrawContext c, int x, int y, int size) {
        rrect(c, x, y, size, size, size / 4, ACCENT);
        rrect(c, x + 1, y + 1, size - 2, size / 2, size / 4, 0x33FFFFFF);
        float s = size / 12f;
        var m = c.getMatrices();
        m.pushMatrix();
        m.translate(x + (size - 6 * s) / 2f, y + (size - 8 * s) / 2f);
        m.scale(s, s);
        textShadow(c, "R", 0, 0, 0xFFFFFFFF);
        m.popMatrix();
    }

    /** Plakietka w prawym dolnym rogu menu pauzy: logo + nick. */
    public static void badge(DrawContext c, MinecraftClient mc, int sw, int sh) {
        String nick = mc.getSession().getUsername();
        int tw = Math.max(width("Rizz Client"), width(nick));
        int w = 8 + 20 + 7 + tw + 10, h = 28;
        int x = sw - w - 8, y = sh - h - 8;
        rrect(c, x - 1, y - 1, w + 2, h + 2, 9, 0x33FFFFFF);
        rrect(c, x, y, w, h, 8, 0xE01C1C22);
        logo(c, x + 6, y + 4, 20);
        text(c, "Rizz Client", x + 33, y + 5, 0xFFFFFFFF);
        text(c, nick, x + 33, y + 15, 0xFFAAAAB4);
    }
}
