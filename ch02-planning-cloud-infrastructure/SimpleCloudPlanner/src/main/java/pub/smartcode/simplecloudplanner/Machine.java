package pub.smartcode.simplecloudplanner;

public class Machine {

    private double cost; // in money/minute
    private double startupTime; // in minutes
    private String configuration; // machine configuration; ignored by planner
    private int id; // machine id; ignored by planner

    public Machine(double cost, double startupTime, String configuration, int id) {
        this.cost = cost;
        this.startupTime = startupTime;
        this.configuration = configuration;
        this.id = id;
    }

    public double getCost() {
        return cost;
    }

    public void setCost(double cost) {
        this.cost = cost;
    }

    public double getStartupTime() {
        return startupTime;
    }

    public void setStartupTime(double startupTime) {
        this.startupTime = startupTime;
    }

    public String getConfiguration() {
        return configuration;
    }

    public void setConfiguration(String configuration) {
        this.configuration = configuration;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    @Override
    public String toString() {
        return String.format(
                "Machine %d %s (startup: %.2f min, cost: $%.6f/min)",
                id, configuration, startupTime, cost);
    }
}
