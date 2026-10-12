package pl.rizz.client;

import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.Click;
import net.minecraft.client.input.KeyInput;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.List;

/** Menu Rizz Client (Prawy Shift) w stylu macOS. */
public class ClickGuiScreen extends Screen {
    private static final int W = 560, H = 360;
    private static Module selected = Modules.ALL.get(0);

    private record Hit(int x, int y, int w, int h, Runnable click, Setting.Num slider) {
        boolean in(double mx, double my) { return mx >= x && mx < x + w && my >= y && my < y + h; }
    }

    private final List<Hit> hits = new ArrayList<>();
    private Hit dragging;

    public ClickGuiScreen() { super(Text.literal("Rizz Client")); }

    @Override public boolean shouldPause() { return false; }

    @Override
    public void render(DrawContext c, int mx, int my, float delta) {
        hits.clear();
        c.fill(0, 0, width, height, 0x77000000);
        int x0 = (width - W) / 2, y0 = (height - H) / 2;

        Gfx.rrect(c, x0 - 1, y0 - 1, W + 2, H + 2, 12, 0x33FFFFFF);
        Gfx.rrect(c, x0, y0, W, H, 11, 0xF01C1C22);

        // sygnalizacja okna jak w macOS
        int[] dots = {0xFFFF5F57, 0xFFFEBC2E, 0xFF28C840};
        for (int i = 0; i < 3; i++) Gfx.rrect(c, x0 + 14 + i * 18, y0 + 12, 12, 12, 6, dots[i]);
        hits.add(new Hit(x0 + 14, y0 + 12, 12, 12, this::close, null));
        Gfx.logo(c, x0 + W / 2 - 40, y0 + 8, 16);
        Gfx.text(c, "Rizz Client", x0 + W / 2 - 20, y0 + 12, 0xFFDDDDE6);

        // pasek boczny z modulami
        Gfx.rrect(c, x0 + 6, y0 + 34, 150, H - 40, 8, 0xFF26262E);
        int ry = y0 + 42;
        for (Module m : Modules.ALL) {
            if (m == selected) Gfx.rrect(c, x0 + 10, ry, 142, 26, 6, 0xFF3A3A46);
            Gfx.text(c, m.name, x0 + 18, ry + 9, m.enabled ? 0xFFFFFFFF : 0xFF9A9AA6);
            Gfx.toggle(c, x0 + 118, ry + 5, m.enabled);
            hits.add(new Hit(x0 + 10, ry, 142, 26, () -> selected = m, null));
            hits.add(new Hit(x0 + 118, ry + 5, 28, 16, m::toggle, null));
            ry += 30;
        }

        // panel ustawien
        int px = x0 + 172, pw = W - 172 - 16, sy = y0 + 90;
        var ms = c.getMatrices();
        ms.pushMatrix();
        ms.translate((float) px, (float) (y0 + 42));
        ms.scale(1.5f, 1.5f);
        Gfx.text(c, selected.name, 0, 0, 0xFFFFFFFF);
        ms.popMatrix();
        Gfx.text(c, selected.description, px, y0 + 62, 0xFF8A8A96);
        Gfx.rrect(c, px, y0 + 76, pw, 1, 0, 0x22FFFFFF);

        for (Setting<?> s : selected.settings) {
            if (s instanceof Setting.Bool b) {
                Gfx.text(c, b.label, px, sy + 9, 0xFFDDDDE6);
                Gfx.toggle(c, px + pw - 28, sy + 5, b.value);
                hits.add(new Hit(px, sy, pw, 26, () -> { b.value = !b.value; Config.save(); }, null));
                sy += 30;
            } else if (s instanceof Setting.Num n) {
                Gfx.text(c, n.label, px, sy, 0xFFDDDDE6);
                String d = n.display();
                Gfx.text(c, d, px + pw - Gfx.width(d), sy, 0xFFAAAAB4);
                int by = sy + 16;
                double t = (n.value - n.min) / (n.max - n.min);
                int fw = (int) (pw * t);
                Gfx.rrect(c, px, by, pw, 6, 3, 0xFF3A3A46);
                if (fw > 0) Gfx.rrect(c, px, by, Math.max(fw, 6), 6, 3, Gfx.ACCENT);
                Gfx.rrect(c, px + fw - 5, by - 2, 10, 10, 5, 0xFFFFFFFF);
                hits.add(new Hit(px, sy + 10, pw, 20, null, n));
                sy += 38;
            } else if (s instanceof Setting.Mode md) {
                Gfx.text(c, md.label, px, sy + 9, 0xFFDDDDE6);
                int bw = 100;
                Gfx.rrect(c, px + pw - bw, sy + 4, bw, 18, 5, 0xFF3A3A46);
                Gfx.centered(c, md.value, px + pw - bw / 2, sy + 9, 0xFFFFFFFF);
                hits.add(new Hit(px + pw - bw, sy + 4, bw, 18, () -> { md.cycle(); Config.save(); }, null));
                sy += 30;
            }
        }

        Gfx.text(c, "Prawy Shift - zamknij  |  Klawisze: Opcje > Sterowanie > Rizz Client", x0 + 172, y0 + H - 16, 0xFF6A6A76);
    }

    private void slide(double mx) {
        Setting.Num n = dragging.slider();
        double t = Math.max(0, Math.min(1, (mx - dragging.x()) / dragging.w()));
        n.set(n.min + t * (n.max - n.min));
    }

    // 1.21.9+: zdarzenia myszy/klawiatury to obiekty Click / KeyInput
    @Override
    public boolean mouseClicked(Click click, boolean doubled) {
        double mx = click.x(), my = click.y();
        if (click.button() == 0) {
            for (int i = hits.size() - 1; i >= 0; i--) {
                Hit h = hits.get(i);
                if (!h.in(mx, my)) continue;
                if (h.slider() != null) { dragging = h; slide(mx); }
                else if (h.click() != null) h.click().run();
                return true;
            }
        }
        return super.mouseClicked(click, doubled);
    }

    @Override
    public boolean mouseDragged(Click click, double offsetX, double offsetY) {
        if (dragging != null) { slide(click.x()); return true; }
        return super.mouseDragged(click, offsetX, offsetY);
    }

    @Override
    public boolean mouseReleased(Click click) {
        if (dragging != null) { dragging = null; Config.save(); return true; }
        return super.mouseReleased(click);
    }

    @Override
    public boolean keyPressed(KeyInput input) {
        if (input.key() == GLFW.GLFW_KEY_RIGHT_SHIFT) { close(); return true; }
        return super.keyPressed(input);
    }
}
