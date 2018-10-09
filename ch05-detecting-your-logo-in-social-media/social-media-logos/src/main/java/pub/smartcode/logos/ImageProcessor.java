package pub.smartcode.logos;

import java.util.Map;
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.Properties;
import java.net.URL;
import java.io.File;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Map;
import java.util.HashMap;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.Set;
import java.util.HashSet;

import org.apache.commons.io.FileUtils;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;
import com.google.common.collect.Lists;

public class ImageProcessor implements Runnable {
    private BlockingQueue<Map<String,Object>> imageQueue;
    private Properties props;
    private Set<String> logos;

    public ImageProcessor(Properties props, BlockingQueue<Map<String,Object>> imageQueue) {
        this.props = props;
        this.imageQueue = imageQueue;
        logos = new HashSet<String>();
        List<String> logoStrings = Lists.newArrayList(
                props.getProperty("logos").split("\\s*,\\s*"));
        for(String s : logoStrings) {
            logos.add(s);
        }
    }

    public void run() {
        Pattern detectionPattern = Pattern.compile("(.*): (\\d+)%");
        try {
            BufferedWriter csvWriter = Files.newBufferedWriter(Paths.get(props.getProperty("csv_out")));
            CSVPrinter csvPrinter = new CSVPrinter(csvWriter, CSVFormat.DEFAULT
                    .withHeader("User", "TweetID", "Time", "Text", "Photo", "Detection", "Confidence"));

            ProcessBuilder builder = new ProcessBuilder(props.getProperty("yolo_cmd"));
            builder.redirectErrorStream(true);
            Process process = builder.start();
            OutputStream stdin = process.getOutputStream();
            InputStream stdout = process.getInputStream();
            BufferedReader reader = new BufferedReader (new InputStreamReader(stdout));
            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(stdin));

            String line = reader.readLine();
            System.out.println(line);
            while(!line.equals("Enter Image Path:")) {
                line = reader.readLine();
                System.out.println(line);
            }

            while(true) {
                Map<String, Object> msgobj = imageQueue.take();
                try {
                    Map<String, Object> entities = (Map<String, Object>)msgobj.get("entities");
                    List<Map<String, Object>> media = (List<Map<String, Object>>)entities.get("media");
                    for(Map<String, Object> entity : media) {
                        String type = (String)entity.get("type");
                        if(type.equals("photo")) {
                            String url = (String)entity.get("media_url");
                            // download photo
                            File destFile = File.createTempFile("logo-", ".jpg");
                            FileUtils.copyURLToFile(new URL(url), destFile);
                            System.out.println("Downloaded " + url + " to " + destFile);
                            writer.write(destFile + "\n");
                            writer.flush();
                            Map<String, Double> detections = new HashMap<String, Double>();
                            line = reader.readLine();
                            System.out.println(line);
                            while(!line.equals("Enter Image Path:")) {
                                line = reader.readLine();
                                System.out.println(line);
                                Matcher m = detectionPattern.matcher(line);
                                if(m.matches() && logos.contains(m.group(1))) {
                                    detections.put(m.group(1), Double.parseDouble(m.group(2))/100.0);
                                }
                            }
                            destFile.delete();
                            for(String k : detections.keySet()) {
                                System.out.println(detections);
                                csvPrinter.printRecord((String)((Map<String, Object>)msgobj.get("user")).get("screen_name"),
                                                       (String)msgobj.get("id_str"),
                                                       (String)msgobj.get("created_at"),
                                                       (String)msgobj.get("text"),
                                                       url, k, detections.get(k));
                                csvPrinter.flush();
                            }
                        }
                    } 
                }
                catch(Exception e) { System.out.println(e); }
            }
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
}


