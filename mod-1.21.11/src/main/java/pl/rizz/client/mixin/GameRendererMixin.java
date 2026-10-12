package pl.rizz.client.mixin;

import net.minecraft.client.render.Camera;
import net.minecraft.client.render.GameRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import pl.rizz.client.Modules;

@Mixin(GameRenderer.class)
public abstract class GameRendererMixin {
    // od 1.21.2 getFov zwraca float
    @Inject(method = "getFov(Lnet/minecraft/client/render/Camera;FZ)F", at = @At("RETURN"), cancellable = true, require = 0)
    private void rizz$fov(Camera camera, float tickProgress, boolean changingFov, CallbackInfoReturnable<Float> cir) {
        if (Modules.ZOOM.zooming()) {
            cir.setReturnValue(cir.getReturnValue() / Modules.ZOOM.factor.value.floatValue());
        }
    }
}
