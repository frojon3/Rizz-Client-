package pl.rizz.client;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.option.Perspective;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public final class Modules {
    public static final Keystrokes KEYSTROKES = new Keystrokes();
    public static final Freelook FREELOOK = new Freelook();
    public static final Zoom ZOOM = new Zoom();
    public static final ToggleSprint TOGGLE_SPRINT = new ToggleSprint();
    public static final InfoHud INFO_HUD = new InfoHud();

    public static final List<Module> ALL = new ArrayList<>(
            List.of(KEYSTROKES, FREELOOK, ZOOM, TOGGLE_SPRINT, INFO_HUD));

    private Modules() {}

    // ------------------------------------------------------------ Keystrokes
    public static class Keystrokes extends Module {
        final Setting.Num x = add(new Setting.Num("x", "Pozycja X (%)", 2, 0, 95, 1));
        final Setting.Num y = add(new Setting.Num("y", "Pozycja Y (%)", 55, 0, 90, 1));
        final Setting.Num scale = add(new Setting.Num("scale", "Skala", 1.0, 0.5, 2.0, 0.1));
        final Setting.Num opacity = add(new Setting.Num("opacity", "Przezroczystosc tla", 0.45, 0.1, 0.9, 0.05));
        final Setting.Bool mouse = add(new Setting.Bool("mouse", "Pokaz LPM / PPM + CPS", true));
        final Setting.Bool space = add(new Setting.Bool("space", "Pokaz spacje", true));

        private static final ArrayDeque<Long> LEFT = new ArrayDeque<>();
        private static final ArrayDeque<Long> RIGHT = new ArrayDeque<>();

        public Keystrokes() { super("Keystrokes", "Wyswietla wcisniete klawisze WASD, myszke i CPS"); }

        public static void click(int button) {
            long n = System.currentTimeMillis();
            if (button == 0) LEFT.add(n);
            else if (button == 1) RIGHT.add(n);
        }

        public static int cps(boolean left) {
            ArrayDeque<Long> q = left ? LEFT : RIGHT;
            long n = System.currentTimeMillis();
            while (!q.isEmpty() && n - q.peekFirst() > 1000) q.pollFirst();
            return q.size();
        }

        private void key(DrawContext c, int px, int py, int w, int h, String label, boolean down) {
            int bg = down ? 0xCCFFFFFF : ((int) (opacity.value * 255) << 24);
            Gfx.rrect(c, px, py, w, h, 4, bg);
            Gfx.centered(c, label, px + w / 2, py + (h - 8) / 2, down ? 0xFF111111 : 0xFFFFFFFF);
        }

        @Override
        public void onHud(DrawContext c, MinecraftClient mc) {
            final int k = 24, g = 2, total = 3 * k + 2 * g;
            float s = scale.value.floatValue();
            int sw = mc.getWindow().getScaledWidth(), sh = mc.getWindow().getScaledHeight();
            int px = (int) Math.min(sw * x.value / 100.0, sw - total * s);
            int py = (int) (sh * y.value / 100.0);

            var m = c.getMatrices();
            m.pushMatrix();
            m.translate((float) px, (float) py);
            m.scale(s, s);
            var o = mc.options;
            key(c, k + g, 0, k, k, "W", o.forwardKey.isPressed());
            key(c, 0, k + g, k, k, "A", o.leftKey.isPressed());
            key(c, k + g, k + g, k, k, "S", o.backKey.isPressed());
            key(c, 2 * (k + g), k + g, k, k, "D", o.rightKey.isPressed());
            int yy = 2 * (k + g);
            if (mouse.value) {
                int w = (total - g) / 2;
                key(c, 0, yy, w, k, "LPM", o.attackKey.isPressed());
                key(c, w + g, yy, w, k, "PPM", o.useKey.isPressed());
                Gfx.centered(c, cps(true) + " CPS", w / 2, yy + k - 10, 0xFFAAAAB4);
                Gfx.centered(c, cps(false) + " CPS", w + g + w / 2, yy + k - 10, 0xFFAAAAB4);
                yy += k + g;
            }
            if (space.value) key(c, 0, yy, total, 14, "---", o.jumpKey.isPressed());
            m.popMatrix();
        }
    }

    // ------------------------------------------------------------ Freelook
    public static class Freelook extends Module {
        public boolean active;
        public float yaw, pitch;
        private Perspective prev;
        private boolean toggled;

        final Setting.Mode mode = add(new Setting.Mode("mode", "Tryb", new String[]{"Przytrzymaj", "Przelacz"}, 0));
        final Setting.Bool third = add(new Setting.Bool("third", "Widok z trzeciej osoby", true));

        public Freelook() { super("Freelook", "Rozgladaj sie bez obracania postaci (klawisz w Sterowaniu)"); }

        @Override
        public void onTick(MinecraftClient mc) {
            if (mc.currentScreen != null) { if (active) stop(mc); return; }
            boolean want;
            if (mode.index() == 0) {
                want = RizzClient.freelookKey.isPressed();
            } else {
                while (RizzClient.freelookKey.wasPressed()) toggled = !toggled;
                want = toggled;
            }
            if (want && !active) start(mc);
            else if (!want && active) stop(mc);
        }

        private void start(MinecraftClient mc) {
            active = true;
            yaw = mc.player.getYaw();
            pitch = mc.player.getPitch();
            if (third.value) {
                prev = mc.options.getPerspective();
                mc.options.setPerspective(Perspective.THIRD_PERSON_BACK);
            }
        }

        private void stop(MinecraftClient mc) {
            active = false;
            toggled = false;
            if (prev != null) { mc.options.setPerspective(prev); prev = null; }
        }

        public void handle(double dx, double dy) {
            yaw += (float) dx * 0.15f;
            pitch = Math.max(-90f, Math.min(90f, pitch + (float) dy * 0.15f));
        }

        @Override
        public void onDisable() {
            if (active) stop(MinecraftClient.getInstance());
        }
    }

    // ------------------------------------------------------------ Zoom
    public static class Zoom extends Module {
        public final Setting.Num factor = add(new Setting.Num("factor", "Przyblizenie (x)", 4.0, 1.5, 10.0, 0.5));

        public Zoom() { super("Zoom", "Przyblizenie na przytrzymanie klawisza (domyslnie C)"); }

        public boolean zooming() {
            return enabled && RizzClient.zoomKey != null && RizzClient.zoomKey.isPressed();
        }
    }

    // ------------------------------------------------------------ Toggle Sprint
    public static class ToggleSprint extends Module {
        public ToggleSprint() { super("Toggle Sprint", "Automatycznie biegniesz gdy idziesz do przodu"); }

        @Override
        public void onTick(MinecraftClient mc) {
            ClientPlayerEntity p = mc.player;
            if (mc.currentScreen == null && mc.options.forwardKey.isPressed() && !p.isSneaking()
                    && !p.horizontalCollision && p.getHungerManager().getFoodLevel() > 6) {
                p.setSprinting(true);
            }
        }
    }

    // ------------------------------------------------------------ Info HUD
    public static class InfoHud extends Module {
        final Setting.Bool fps = add(new Setting.Bool("fps", "FPS", true));
        final Setting.Bool cps = add(new Setting.Bool("cps", "CPS", true));
        final Setting.Bool coords = add(new Setting.Bool("coords", "Koordynaty", true));
        final Setting.Num x = add(new Setting.Num("x", "Pozycja X (%)", 1, 0, 95, 1));
        final Setting.Num y = add(new Setting.Num("y", "Pozycja Y (%)", 2, 0, 95, 1));

        public InfoHud() { super("Info HUD", "FPS, CPS i koordynaty na ekranie"); }

        @Override
        public void onHud(DrawContext c, MinecraftClient mc) {
            List<String> lines = new ArrayList<>();
            if (fps.value) lines.add("FPS: " + mc.getCurrentFps());
            if (cps.value) lines.add("CPS: " + Keystrokes.cps(true) + " | " + Keystrokes.cps(false));
            if (coords.value) lines.add(String.format("XYZ: %.0f %.0f %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
            if (lines.isEmpty()) return;
            int w = 0;
            for (String l : lines) w = Math.max(w, Gfx.width(l));
            int px = (int) (mc.getWindow().getScaledWidth() * x.value / 100.0);
            int py = (int) (mc.getWindow().getScaledHeight() * y.value / 100.0);
            Gfx.rrect(c, px, py, w + 10, lines.size() * 11 + 5, 5, 0x88000000);
            int ly = py + 4;
            for (String l : lines) { Gfx.textShadow(c, l, px + 5, ly, 0xFFFFFFFF); ly += 11; }
        }
    }
}
