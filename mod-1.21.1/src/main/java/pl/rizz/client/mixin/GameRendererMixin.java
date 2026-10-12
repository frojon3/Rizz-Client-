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
    // Zoom: zmniejszamy FOV
    @Inject(method = "getFov", at = @At("RETURN"), cancellable = true)
    private void rizz$fov(Camera camera, float tickDelta, boolean changingFov, CallbackInfoReturnable<Double> cir) {
        if (Modules.ZOOM.zooming()) {
            cir.setReturnValue(cir.getReturnValue() / Modules.ZOOM.factor.value);
        }
    }
}
