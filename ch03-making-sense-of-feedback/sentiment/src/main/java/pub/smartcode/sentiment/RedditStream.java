package pub.smartcode.sentiment;

import com.google.common.collect.Lists;
import net.dean.jraw.RedditClient;
import net.dean.jraw.http.NetworkAdapter;
import net.dean.jraw.http.OkHttpNetworkAdapter;
import net.dean.jraw.http.UserAgent;
import net.dean.jraw.models.PublicContribution;
import net.dean.jraw.models.Submission;
import net.dean.jraw.oauth.Credentials;
import net.dean.jraw.oauth.OAuthHelper;
import net.dean.jraw.pagination.SearchPaginator;
import net.dean.jraw.tree.CommentNode;
import net.dean.jraw.tree.RootCommentNode;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.Properties;
import java.net.SocketException;

public class RedditStream implements Runnable {
    private RedditClient reddit;
    private SentimentDetector sentimentDetector;
    private ArrayList<String> terms;
    private Properties props;

    public RedditStream(SentimentDetector sentimentDetector,
                        Properties props) {
        this.sentimentDetector = sentimentDetector;
        terms = Lists.newArrayList(
                props.getProperty("reddit_terms")
                        .split("\\s*,\\s*"));
        this.props = props;
        setupConnection();
    }

    public void setupConnection() {
        UserAgent userAgent = new UserAgent("bot", "pub.smartcode.sentiment", "v0.1", props.getProperty("reddit_user"));
        Credentials credentials = Credentials.script(
                props.getProperty("reddit_user"),
                props.getProperty("reddit_password"),
                props.getProperty("reddit_clientid"),
                props.getProperty("reddit_clientsecret"));
        NetworkAdapter adapter = new OkHttpNetworkAdapter(userAgent);
        reddit = OAuthHelper.automatic(adapter, credentials);
    }

    public void run() {
        try {
            while (true) {
                try {
                    for (String term : terms) {
                        SearchPaginator result =
                            reddit.search().query(term).build();
                        for (Submission s : result.next()) {
                            if(!sentimentDetector.alreadyProcessed(s.getId())) {
                                sentimentDetector.detectSentiment(
                                        s.getId(),
                                        s.getTitle(),
                                        "reddit",
                                        true, true);
                                if (s.getSelfText() != null) {
                                    sentimentDetector.detectSentiment(
                                            s.getId() + "text",
                                            s.getSelfText(),
                                            "reddit",
                                            true, true);
                                }

                                RootCommentNode comments = s.toReference(reddit)
                                    .comments();
                                Iterator<CommentNode<PublicContribution<?>>> it =
                                    comments.walkTree().iterator();
                                while (it.hasNext()) {
                                    PublicContribution<?> thing = it.next().getSubject();

                                    if (thing.getBody() != null &&
                                            !sentimentDetector.alreadyProcessed(thing.getId())) {
                                        // look for at least one search term in comment
                                        boolean containsTerm = false;
                                        String body = thing.getBody();
                                        for(String t : terms) {
                                            if(body.indexOf(t) != -1) {
                                                containsTerm = true;
                                                break;
                                            }
                                        }
                                        if(containsTerm) {
                                            sentimentDetector.detectSentiment(
                                                    thing.getId(),
                                                    body,
                                                    "reddit",
                                                    true, true);
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch(Exception e) {
                    setupConnection();
                }
                // sleep 10 minutes
                Thread.sleep(600000);
            }
        } catch (InterruptedException e) {
        }
    }
}
