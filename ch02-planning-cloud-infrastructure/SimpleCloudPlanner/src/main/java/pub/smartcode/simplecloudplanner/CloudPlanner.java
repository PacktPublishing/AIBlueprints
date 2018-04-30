package pub.smartcode.simplecloudplanner;

import org.optaplanner.core.api.domain.solution.*;
import org.optaplanner.core.api.domain.solution.drools.*;
import org.optaplanner.core.api.domain.valuerange.*;
import org.optaplanner.core.api.score.buildin.hardsoft.*;
import java.util.List;

@PlanningSolution
public class CloudPlanner {

    private List<Machine> machineList;
    private List<Task> taskList;

    private HardSoftScore score;

    public CloudPlanner() {
    }

    public CloudPlanner(List<Machine> machineList, List<Task> taskList) {
        this.machineList = machineList;
        this.taskList = taskList;
    }

    @ValueRangeProvider(id = "machineRange")
    @ProblemFactCollectionProperty
    public List<Machine> getMachineList() {
        return machineList;
    }

    // this list is generated from the Main class
    public void setMachineList(List<Machine> machineList) {
        this.machineList = machineList;
    }

    @PlanningEntityCollectionProperty
    public List<Task> getTaskList() {
        return taskList;
    }

    // this list is generated from the Main class
    public void setTaskList(List<Task> taskList) {
        this.taskList = taskList;
    }

    @PlanningScore
    public HardSoftScore getScore() {
        return score;
    }

    public void setScore(HardSoftScore score) {
        this.score = score;
    }
}

