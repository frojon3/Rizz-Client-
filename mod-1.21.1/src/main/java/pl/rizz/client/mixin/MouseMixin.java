package pl.rizz.client.mixin;

import net.minecraft.client.Mouse;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pl.rizz.client.Modules;

@Mixin(Mouse.class)
public abstract class MouseMixin {
    // licznik CPS dla Keystrokes / Info HUD
    @Inject(method = "onMouseButton", at = @At("HEAD"))
    private void rizz$click(long window, int button, int action, int mods, CallbackInfo ci) {
        if (action == 1) Modules.Keystrokes.click(button);
    }
}
