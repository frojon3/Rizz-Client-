package pl.rizz.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.fabricmc.loader.api.FabricLoader;

import java.nio.file.Files;
import java.nio.file.Path;

public final class Config {
    private static final Path FILE = FabricLoader.getInstance().getConfigDir().resolve("rizzclient.json");
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public static void load() {
        try {
            if (!Files.exists(FILE)) return;
            JsonObject root = JsonParser.parseString(Files.readString(FILE)).getAsJsonObject();
            for (Module m : Modules.ALL) {
                if (!root.has(m.name)) continue;
                JsonObject o = root.getAsJsonObject(m.name);
                if (o.has("enabled")) m.enabled = o.get("enabled").getAsBoolean();
                for (Setting<?> s : m.settings) if (o.has(s.id)) s.load(o.get(s.id));
            }
        } catch (Exception ignored) {}
    }

    public static void save() {
        try {
            JsonObject root = new JsonObject();
            for (Module m : Modules.ALL) {
                JsonObject o = new JsonObject();
                o.addProperty("enabled", m.enabled);
                for (Setting<?> s : m.settings) s.save(o);
                root.add(m.name, o);
            }
            Files.writeString(FILE, GSON.toJson(root));
        } catch (Exception ignored) {}
    }
}
