package pub.smartcode.simplecloudplanner;

import org.optaplanner.core.api.score.buildin.hardsoft.*;
import org.optaplanner.core.impl.score.director.easy.*;

import java.util.*;

public class Scorer implements EasyScoreCalculator<CloudPlanner> {

    public HardSoftScore calculateScore(CloudPlanner cloudPlanner) {

        // accumulate data about the tasks running on each machine
        Map<Machine, List<Task>> machineTasks =
                new HashMap<Machine, List<Task>>();
        // go through each task
        for(Task task : cloudPlanner.getTaskList()) {
            if(task.getMachine() != null) {
                if (!machineTasks.containsKey(task.getMachine())) {
                    machineTasks.put(task.getMachine(),
                            new LinkedList<Task>());
                }
                machineTasks.get(task.getMachine()).add(task);
            }
        }

        // Now compute how long each machine will run
        Map<Machine, Double> machineRuntimes =
                new HashMap<Machine, Double>();
        // go through each machine
        for(Machine machine : machineTasks.keySet()) {
            double time = machine.getStartupTime();
            for(Task task : machineTasks.get(machine)) {
                time += task.getMachineTiming(
                        machine.getConfiguration());
            }
            machineRuntimes.put(machine, time);
        }

        // Find max machine time (all machines run in parallel),
        // and find total cost
        double maxRuntime = 0.0;
        double totalCost = 0.0;
        for(Machine machine : machineRuntimes.keySet()) {
            if(machineRuntimes.get(machine) > maxRuntime) {
                maxRuntime = machineRuntimes.get(machine);
            }
            totalCost += machineRuntimes.get(machine) *
                    machine.getCost();
        }

        // round-off double values to ints for scoring

        // hard score: refuse to spend more than $2;
        // times 1000 for higher precision
        int hardScore = 0;
        if(totalCost > 2.0) {
            hardScore = (int) (-totalCost * 1000);
        }

        // soft score: prefer completion in < 60 mins
        // and prefer to use no more than 10 machines
        // and prefer to spend about $1.50 or less;
        // times 10000 for higher precision
        Double[] ratios = {1.0,
                maxRuntime/60.0,
                machineRuntimes.keySet().size()/10.0,
                totalCost/1.50};
        double maxRatio = Collections.max(Arrays.asList(ratios));
        int softScore = (int)(10000 * (1.0 - maxRatio));

        return HardSoftScore.valueOf(
                hardScore,
                softScore);
    }
}
