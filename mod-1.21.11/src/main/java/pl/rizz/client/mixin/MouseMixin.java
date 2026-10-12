package pl.rizz.client.mixin;

import net.minecraft.client.Mouse;
import net.minecraft.client.input.MouseInput;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pl.rizz.client.Modules;

@Mixin(Mouse.class)
public abstract class MouseMixin {
    // 1.21.9+: onMouseButton(long window, MouseInput input, int action)
    @Inject(method = "onMouseButton(JLnet/minecraft/client/input/MouseInput;I)V", at = @At("HEAD"), require = 0)
    private void rizz$click(long window, MouseInput input, int action, CallbackInfo ci) {
        if (action == 1) Modules.Keystrokes.click(input.button());
    }
}
