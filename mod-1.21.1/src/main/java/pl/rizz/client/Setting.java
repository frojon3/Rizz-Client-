package pl.rizz.client;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

public abstract class Setting<T> {
    public final String id, label;
    public T value;

    protected Setting(String id, String label, T def) {
        this.id = id;
        this.label = label;
        this.value = def;
    }

    public abstract void load(JsonElement e);
    public abstract void save(JsonObject o);

    public static class Bool extends Setting<Boolean> {
        public Bool(String id, String label, boolean def) { super(id, label, def); }
        public void load(JsonElement e) { value = e.getAsBoolean(); }
        public void save(JsonObject o) { o.addProperty(id, value); }
    }

    public static class Num extends Setting<Double> {
        public final double min, max, step;

        public Num(String id, String label, double def, double min, double max, double step) {
            super(id, label, def);
            this.min = min; this.max = max; this.step = step;
        }

        public void set(double v) {
            v = Math.max(min, Math.min(max, v));
            v = Math.round((v - min) / step) * step + min;
            value = Math.round(v * 10000.0) / 10000.0;
        }

        public String display() {
            return step >= 1 ? String.valueOf(value.intValue()) : String.format("%.2f", value);
        }

        public void load(JsonElement e) { set(e.getAsDouble()); }
        public void save(JsonObject o) { o.addProperty(id, value); }
    }

    public static class Mode extends Setting<String> {
        public final String[] modes;

        public Mode(String id, String label, String[] modes, int def) {
            super(id, label, modes[def]);
            this.modes = modes;
        }

        public int index() {
            for (int i = 0; i < modes.length; i++) if (modes[i].equals(value)) return i;
            return 0;
        }

        public void cycle() { value = modes[(index() + 1) % modes.length]; }
        public void load(JsonElement e) { String s = e.getAsString(); for (String m : modes) if (m.equals(s)) value = s; }
        public void save(JsonObject o) { o.addProperty(id, value); }
    }
}
