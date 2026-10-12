package pl.rizz.client.mixin;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pl.rizz.client.Modules;

@Mixin(Entity.class)
public abstract class EntityMixin {
    @Inject(method = "changeLookDirection(DD)V", at = @At("HEAD"), cancellable = true, require = 0)
    private void rizz$look(double dx, double dy, CallbackInfo ci) {
        if (Modules.FREELOOK.active && (Object) this == MinecraftClient.getInstance().player) {
            Modules.FREELOOK.handle(dx, dy);
            ci.cancel();
        }
    }
}
