
// javac -cp surus-0.1.4.jar WikipediaDemo.java
// java -cp .:surus-0.1.4.jar WikipediaDemo

import org.surus.math.RPCA;

import java.io.BufferedReader;
import java.io.FileReader;

class WikipediaDemo {

    public static void printMatrix(double[][] matrix) {
        for(int i = 0; i < matrix.length; i++) {
            for(int j = 0; j < matrix[0].length; j++) {
                System.out.print(" " + matrix[i][j]);
            }
            System.out.println();
        }
    }

    public static double findMin(double[] vals) {
        double min = vals[0];
        for(int i = 0; i < vals.length; i++) {
            if(vals[i] < min) min = vals[i];
        }
        return min;
    }

    public static double findMax(double[] vals) {
        double max = vals[0];
        for(int i = 0; i < vals.length; i++) {
            if(vals[i] > max) max = vals[i];
        }
        return max;
    }

    public static void main(String[] args) {

        // file wikipedia_pages_english.csv has 18297 rows and 550 columns
        int rows = 18297;
        int cols = 550;
        double [][] pageViews = new double[rows][cols];
        try(BufferedReader br = new BufferedReader(new FileReader("wikipedia_pages_english.csv"))) {
            String line = br.readLine();
            int row = 0;
            while (line != null) {
                String[] vals = line.split(" ");
                for(int col = 0; col < cols; col++) {
                    pageViews[row][col] = Double.parseDouble(vals[col]);
                }
                row++;
                if(row >= rows) break;
                line = br.readLine();
            }
        } catch(Exception e) { e.printStackTrace(); }

        System.out.println("Loaded matrix.");

        double[] maxs = new double[rows];
        double[] mins = new double[rows];

        // rescale matrix so each row is between 0 and 1
        for(int row = 0; row < rows; row++) {
            maxs[row] = findMax(pageViews[row]);
            mins[row] = findMin(pageViews[row]);
            //System.out.println("Row " + row + ", min = " + mins[row] + ", max = " + maxs[row]);
            for(int col = 0; col < cols; col++) {
                pageViews[row][col] = (pageViews[row][col] - mins[row]) / (maxs[row] - mins[row]);
            }
        }

        System.out.println("Rescaled matrix.");

        RPCA rpca = new RPCA(pageViews, 1, 6.0/Math.sqrt(18297));

        double[][] E = rpca.getE().getData();
        double[][] S = rpca.getS().getData();
        double[][] L = rpca.getL().getData();

        System.out.println("E:");
        printMatrix(E);
        System.out.println("S:");
        printMatrix(S);
        System.out.println("L:");
        printMatrix(L);

        // find anomalies in S
        for(int row = 0; row < rows; row++) {
            for(int col = 0; col < cols; col++) {
                if(S[row][col] > 0.00001) {
                    System.out.println("Anomaly: row = " + row + ", col = " + col + ", S = " + S[row][col] +
                                       ", row min = " + mins[row] + ", row max = " + maxs[row] + ", value = " + pageViews[row][col] + ", orig value = " +
                                       ((pageViews[row][col]*(maxs[row]-mins[row]))+mins[row]));
                }
            }
        }
    }
}

