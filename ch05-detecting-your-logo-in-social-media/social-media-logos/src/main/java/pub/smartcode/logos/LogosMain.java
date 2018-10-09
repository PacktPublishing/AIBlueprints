package pub.smartcode.logos;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import com.google.gson.Gson;

public class LogosMain
{
    public static void main( String[] args ) throws Exception
    {
        Properties props = new Properties();
        try {
            props.load(new FileInputStream("config.properties"));
        } catch(IOException e) {
            System.out.println(e);
            System.exit(-1);
        }

        Gson gson = new Gson();
        BlockingQueue<Map<String,Object>> imageQueue = new LinkedBlockingQueue<Map<String,Object>>(100000);

        TwitterStream twitterStream = new TwitterStream(gson, props, imageQueue);
        ImageProcessor imageProcessor = new ImageProcessor(props, imageQueue);

        Thread twitterStreamThread = new Thread(twitterStream);
        Thread imageProcessorThread = new Thread(imageProcessor);

        twitterStreamThread.start();
        imageProcessorThread.start();

        twitterStreamThread.join();
        imageProcessorThread.join();
    }
}
