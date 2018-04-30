package pub.smartcode.simplecloudplanner;

import org.optaplanner.core.api.solver.Solver;
import org.optaplanner.core.api.solver.SolverFactory;
import java.util.*;

public class Main {
    public static void main(String[] args) {

        List<Machine> machineList = new ArrayList<Machine>();

        // AWS EC2 pricing: https://aws.amazon.com/ec2/pricing
        // (on-demand pricing used here, time units = minutes)
        // create 20 of each type (not all will necessarily be used);
        // don't create more than AWS limits allow
        int machineid = 0;
        for(int i = 0; i < 20; i++) {
            // startup: 218.07 secs
            machineList.add(new Machine(0.1000/60.0, 3.6, "m4.large", machineid));
            machineid++;
            // startup: 155.20 secs
            machineList.add(new Machine(0.2000/60.0, 2.6, "m4.xlarge", machineid));
            machineid++;
            // startup: 135.15 secs
            machineList.add(new Machine(0.1000/60.0, 2.3, "c4.large", machineid));
            machineid++;
            // startup: 134.28 secs
            machineList.add(new Machine(0.1990/60.0, 2.3, "c4.xlarge", machineid));
            machineid++;
            // startup: 189.66 secs
            machineList.add(new Machine(0.3980/60.0, 3.2, "c4.2xlarge", machineid));
            machineid++;
        }

        // generate tasks; in our case, image ids
        int taskid = 1;
        ArrayList<Task> tasks = new ArrayList<Task>();
        for(int imageid = 1322; imageid <= 1599; imageid++) {
            Task t = new Task(String.valueOf(imageid), taskid, null);

            // benchmark data: time to complete a task on each machine
            // (time units = minutes)

            // three runs: 2:42.80 2:36.34 2:37.15
            t.setMachineTiming("m4.large", 2.65);

            // three runs: 1:43.98 1:32.22 1:31.21
            t.setMachineTiming("m4.xlarge", 1.60);

            // three runs: 2:21.64 2:41.51 2:35.87
            t.setMachineTiming("c4.large", 2.55);

            // three runs: 1:37.34 1:25.28 1:27.68
            t.setMachineTiming("c4.xlarge", 1.50);

            // three runs: 1:12.32 1:02.30 1:01.89
            t.setMachineTiming("c4.2xlarge", 1.09);

            tasks.add(t);
            taskid++;
        }

        SolverFactory<CloudPlanner> solverFactory =
                SolverFactory.createFromXmlResource(
                        "simpleCloudPlannerConfig.xml");
        Solver<CloudPlanner> solver = solverFactory.buildSolver();

        CloudPlanner unsolvedCloudPlanner = new CloudPlanner();
        unsolvedCloudPlanner.setMachineList(machineList);
        unsolvedCloudPlanner.setTaskList(tasks);

        CloudPlanner solvedCloudPlanner =
                solver.solve(unsolvedCloudPlanner);

        System.out.println("Best plan:");
        for(Task task : solvedCloudPlanner.getTaskList()) {
            System.out.println(task + " - " + task.getMachine());
        }
        System.out.println("---");
        double totalCost = 0.0;
        double maxTime = 0.0;
        Map<Machine, List<Task>> machineTasks =
                new HashMap<Machine, List<Task>>();
        // go through each task
        for(Task task : solvedCloudPlanner.getTaskList()) {
            if(task.getMachine() != null) {
                if (!machineTasks.containsKey(task.getMachine())) {
                    machineTasks.put(task.getMachine(),
                            new LinkedList<Task>());
                }
                machineTasks.get(task.getMachine()).add(task);
            }
        }
        // go through each machine
        for(Machine machine : machineTasks.keySet()) {
            double time = machine.getStartupTime();
            for(Task task : machineTasks.get(machine)) {
                time += task.getMachineTiming(
                        machine.getConfiguration());
            }
            double cost = time * machine.getCost();
            System.out.format("Machine time for %s: " +
                            "%.2f min (cost: $%.4f), tasks: %d\n",
                    machine, time, cost,
                    machineTasks.get(machine).size());
            totalCost += cost;
            // save the time of the longest-running machine
            if(time > maxTime) { maxTime = time; }
        }
        System.out.println("---");
        System.out.println("Machine count: " +
                machineTasks.keySet().size());
        System.out.format("Total cost: $%.2f\n", totalCost);
        System.out.format("Total time (if run in parallel): %.2f\n",
                maxTime);
        System.out.println();

        // print aws run script

        for(Machine machine : machineTasks.keySet()) {
            String taskList = "";
            for(Task task : machineTasks.get(machine)) {
                taskList += " " + task.getTaskType();
            }
            System.out.format(
                    "bash ./setup-and-run.sh %s %d %s &\n",
                    machine.getConfiguration(), machine.getId(),
                    taskList);
        }
    }
}
