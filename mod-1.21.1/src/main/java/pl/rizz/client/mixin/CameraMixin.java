package pl.rizz.client.mixin;

import net.minecraft.client.render.Camera;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import pl.rizz.client.Modules;

@Mixin(Camera.class)
public abstract class CameraMixin {
    @ModifyVariable(method = "setRotation", at = @At("HEAD"), ordinal = 0, argsOnly = true)
    private float rizz$yaw(float yaw) {
        return Modules.FREELOOK.active ? Modules.FREELOOK.yaw : yaw;
    }

    @ModifyVariable(method = "setRotation", at = @At("HEAD"), ordinal = 1, argsOnly = true)
    private float rizz$pitch(float pitch) {
        return Modules.FREELOOK.active ? Modules.FREELOOK.pitch : pitch;
    }
}
