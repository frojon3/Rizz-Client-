package pl.rizz.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.GameMenuScreen;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import org.lwjgl.glfw.GLFW;

public class RizzClient implements ClientModInitializer {
    public static KeyBinding menuKey, freelookKey, zoomKey;

    @Override
    public void onInitializeClient() {
        Config.load();

        menuKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.rizzclient.menu", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_RIGHT_SHIFT, "category.rizzclient"));
        freelookKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.rizzclient.freelook", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_LEFT_ALT, "category.rizzclient"));
        zoomKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.rizzclient.zoom", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_C, "category.rizzclient"));

        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            while (menuKey.wasPressed()) {
                if (mc.currentScreen == null) mc.setScreen(new ClickGuiScreen());
            }
            if (mc.player == null) return;
            for (Module m : Modules.ALL) if (m.enabled) m.onTick(mc);
        });

        HudRenderCallback.EVENT.register((ctx, tickCounter) -> {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc.player == null || mc.options.hudHidden) return;
            for (Module m : Modules.ALL) if (m.enabled) m.onHud(ctx, mc);
        });

        // logo + nick w prawym dolnym rogu menu pauzy (ESC)
        ScreenEvents.AFTER_INIT.register((client, screen, w, h) -> {
            if (screen instanceof GameMenuScreen) {
                ScreenEvents.afterRender(screen).register((s, ctx, mx, my, delta) ->
                        Gfx.badge(ctx, client, s.width, s.height));
            }
        });
    }
}
