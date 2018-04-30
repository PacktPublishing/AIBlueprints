package pub.smartcode.sentiment;

import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.neural.rnn.RNNCoreAnnotations;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import edu.stanford.nlp.sentiment.SentimentCoreAnnotations;
import edu.stanford.nlp.trees.Tree;
import edu.stanford.nlp.util.CoreMap;
import org.ejml.simple.SimpleMatrix;

import java.io.*;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.logging.Level;
import java.util.logging.Logger;

public class SentimentDetector {

    private StanfordCoreNLP pipeline;
    private Connection db;
    private Logger logger;
    private Map<String, Double> adjectives;

    public SentimentDetector(Connection db) {
        this.db = db;
        Properties props = new Properties();
        props.setProperty("annotators", "tokenize, ssplit, pos, parse, sentiment");
        pipeline = new StanfordCoreNLP(props);
        logger = Logger.getLogger("SentimentDetector");
        adjectives = new HashMap<String, Double>();
        try {
            BufferedReader adjfile = new BufferedReader(
                    new InputStreamReader(
                            new FileInputStream("adjectives/2000.tsv")));
            String line = adjfile.readLine();
            while(line != null) {
                String[] fields = line.split("\\t");
                if(fields.length == 3) {
                    adjectives.put(fields[0], Double.parseDouble(fields[1]));
                }
                line = adjfile.readLine();
            }
            adjfile.close();
        } catch(IOException e) {
            logger.log(Level.SEVERE, e.toString());
        }
    }

    public boolean alreadyProcessed(String msgId) {
        try {
            String sql = "SELECT 1 FROM sentiment WHERE id like ?";
            PreparedStatement pstmt = db.prepareStatement(sql);
            // append -% to like query arg because id's actually
            // have a sentencie # attached at the end
            pstmt.setString(1, msgId + "-%");
            pstmt.execute();
            return pstmt.getResultSet().next();
        } catch(SQLException e) {
            logger.log(Level.SEVERE, e.getMessage());
            return false;
        }
    }

    public void detectSentiment(String msgId, String txt, String source,
                                boolean useCoreNLP, boolean saveDb) {
        Annotation annotation = new Annotation(txt);
        pipeline.annotate(annotation);
        List<CoreMap> sentences = annotation.get(CoreAnnotations.SentencesAnnotation.class);
        if (sentences != null) {
            int sentNum = 0;
            for (CoreMap sentence : sentences) {
                sentNum++;
                String sentStr = sentence.toString();
                String sentiment = "Neutral";
                int sentiment_num = 2;
                double score = 0.0;
                if(useCoreNLP) {
                    sentiment = sentence.get(SentimentCoreAnnotations.SentimentClass.class);
                    Tree sentimentTree = sentence.get(SentimentCoreAnnotations.SentimentAnnotatedTree.class);
                    // 0 = very negative, 1 = negative, 2 = neutral, 3 = positive, and 4 = very positive
                    Integer predictedClass = RNNCoreAnnotations.getPredictedClass(sentimentTree);
                    SimpleMatrix scoreMatrix = RNNCoreAnnotations.getPredictions(sentimentTree);
                    score = scoreMatrix.get(predictedClass.intValue(), 0);
                    sentiment_num = predictedClass.intValue();
                } else {
                    double sentimentValue = 0.0;
                    int adjectivesFound = 0;
                    // check every adjective to see if it appears in sentence
                    for(String adj : adjectives.keySet()) {
                        if(sentStr.matches(".*\\b" + adj + "\\b.*")) {
                            sentimentValue += adjectives.get(adj);
                            adjectivesFound++;
                        }
                    }
                    if(adjectivesFound > 0) {
                        sentimentValue /= adjectivesFound;
                    }
                    if(sentimentValue < -2) {
                        sentiment = "Very Negative";
                        sentiment_num = 0;
                    } else if(sentimentValue < -0.5) {
                        sentiment = "Negative";
                        sentiment_num = 1;
                    } else if(sentimentValue < 0.5) {
                        sentiment = "Neutral";
                        sentiment_num = 2;
                    } else if(sentimentValue < 2) {
                        sentiment = "Positive";
                        sentiment_num = 3;
                    } else {
                        sentiment = "Very Positive";
                        sentiment_num = 4;
                    }
                    if(adjectivesFound > 0)
                        score = 1.0;
                    else
                        score = 0.0;
                }

                logger.log(Level.INFO, source + " "
                        + msgId + " - "
                        + sentiment + " (" + score + ") "
                        + sentence.toString());

                // Only save somewhat confident, non-neutral results
                if(score > 0.3 && sentiment_num != 2 && saveDb) {
                    try {
                        // check if
                        String sql = "INSERT INTO sentiment"
                                + "(id,source,msg,sentiment,sentiment_num,score)"
                                + " VALUES(?,?,?,?,?,?)";
                        PreparedStatement pstmt = db.prepareStatement(sql);
                        pstmt.setString(1, msgId + "-" + sentNum);
                        pstmt.setString(2, source);
                        pstmt.setString(3, sentStr);
                        pstmt.setString(4, sentiment);
                        pstmt.setInt(5, sentiment_num);
                        pstmt.setDouble(6, score);
                        pstmt.executeUpdate();
                    } catch (SQLException e) {
                        logger.log(Level.SEVERE, e.getMessage());
                    }
                }
            }
        }
    }
}
