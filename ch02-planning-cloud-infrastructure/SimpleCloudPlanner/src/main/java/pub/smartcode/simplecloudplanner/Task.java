package pub.smartcode.simplecloudplanner;

import org.optaplanner.core.api.domain.entity.PlanningEntity;
import org.optaplanner.core.api.domain.variable.PlanningVariable;

import java.util.HashMap;
import java.util.Map;

@PlanningEntity
public class Task {

    private String taskType;
    private int id;
    private Map<String, Double> machineTimings;

    // planning variable
    private Machine machine;

    public Task() {
        machineTimings = new HashMap<String, Double>();
    }

    public Task(String taskType, int id, Machine machine) {
        this.taskType = taskType;
        this.id = id;
        this.machine = machine;
        this.machineTimings = new HashMap<String, Double>();
    }

    public void setMachineTiming(String machineConfig, Double time) {
        machineTimings.put(machineConfig, time);
    }

    public Double getMachineTiming(String machineConfig) {
        if(machineTimings.containsKey(machineConfig)) {
            return machineTimings.get(machineConfig);
        } else {
            return Double.MAX_VALUE;
        }
    }

    @PlanningVariable(valueRangeProviderRefs = {"machineRange"})
    public Machine getMachine() {
        return machine;
    }

    public void setMachine(Machine machine) {
        this.machine = machine;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getTaskType() {
        return taskType;
    }

    public void setTaskType(String taskType) {
        this.taskType = taskType;
    }

    @Override
    public String toString() {
        return "Task " + id + " " + taskType;
    }
}
