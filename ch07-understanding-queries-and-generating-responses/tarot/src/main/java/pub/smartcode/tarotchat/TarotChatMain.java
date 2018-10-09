
package pub.smartcode.tarotchat;

import simplenlg.framework.*;
import simplenlg.lexicon.*;
import simplenlg.realiser.english.*;
import simplenlg.phrasespec.*;
import simplenlg.features.*;
import org.apache.commons.lang3.StringUtils;
import com.mashape.unirest.request.*;
import com.mashape.unirest.http.*;
import com.mashape.unirest.http.exceptions.*;
import org.json.*;
import java.util.*;
import java.util.regex.*;
import java.io.*;

public class TarotChatMain {

    public static String findCourseInText(String input) {
        Matcher m = Pattern.compile("(?i)(?:csci|computer science|comp sci)\\s*(\\d{3})").matcher(input);
        if(m.find()) {
            return "csci" + m.group(1);
        }
        m = Pattern.compile("(?i)(?:cis|cinf|computer information systems)\\s*(\\d{3})").matcher(input);
        if(m.find()) {
            return "cinf" + m.group(1);
        }
        m = Pattern.compile("(?i)(?:math|mathematics)\\s*(\\d{3})").matcher(input);
        if(m.find()) {
            return "math" + m.group(1);
        }
        return "?";
    }

    public static String respondPlannedSemesters(
            NLGFactory nlgFactory, Realiser realiser,
            String planned_semesters) {

        DocumentElement par = nlgFactory.createParagraph();

        Pattern semesterPattern = Pattern.compile("\\((\\d{4}),(\\w+),\\[(.*?)\\]\\)");
        Pattern classPattern = Pattern.compile("\\((\\w+),[^,]+,[^,]+\\)");

        Matcher semesterMatcher = semesterPattern.matcher(planned_semesters);
        while(semesterMatcher.find()) {
            String year = semesterMatcher.group(1);
            String sem = semesterMatcher.group(2);
            String classes = semesterMatcher.group(3);

            SPhraseSpec p = nlgFactory.createClause();
            p.addFrontModifier("In " + StringUtils.capitalize(sem) + " " + year + ",");
            p.setSubject("you");
            p.setVerb("take");
            p.setFeature(Feature.MODAL, "should");

            //System.out.println("Year = " + year + ", sem = " + sem + ", classes = " + classes);
            Map<String, Integer> classCount = new HashMap<String, Integer>();
            Matcher classMatcher = classPattern.matcher(classes);
            while(classMatcher.find()) {
                String c = classMatcher.group(1).toUpperCase();
                if(classCount.containsKey(c)) {
                    classCount.put(c, classCount.get(c) + 1);
                } else {
                    classCount.put(c, new Integer(1));
                }
            }
            //System.out.println(classCount);
            CoordinatedPhraseElement classCoord = new CoordinatedPhraseElement();
            for(String c : classCount.keySet()) {
                if(c.equals("FREE")) { continue; } // add at the end
                classCoord.addCoordinate(c);
            }
            if(classCount.containsKey("FREE")) {
                if(classCount.get("FREE").equals(1)) {
                    classCoord.addCoordinate("a general ed");
                } else {
                    classCoord.addCoordinate(classCount.get("FREE") + " general eds");
                }
            }
            p.setObject(classCoord);
            par.addComponent(p);
        }
        return realiser.realiseSentence(par);
    }

    public static String respondPrereqs(
            NLGFactory nlgFactory, Realiser realiser,
            String course, List<String> prereqs) {

        System.out.println(prereqs);
        if(prereqs.get(0).equals("[]")) {
            return course.toUpperCase() + " has no prerequisites.";
        }

        SPhraseSpec p = nlgFactory.createClause();
        NPPhraseSpec subject = nlgFactory.createNounPhrase("the", "prerequisite");
        if(prereqs.size() > 1) {
            subject.setPlural(true);
            p.setPlural(true);
        }
        PPPhraseSpec prep = nlgFactory.createPrepositionPhrase("for",
                nlgFactory.createNounPhrase(course.toUpperCase()));
        p.setSubject(subject);
        p.addPreModifier(prep);
        p.setVerb("is");
        CoordinatedPhraseElement prereqOptions = new CoordinatedPhraseElement();
        prereqOptions.setFeature(Feature.CONJUNCTION, "or");
        Pattern coursePattern = Pattern.compile("([a-z]{4}[0-9]{3})");
        for(int i = 0; i < Math.min(prereqs.size(), 3); i++) {
            String pr = prereqs.get(i);
            CoordinatedPhraseElement prereqsConj = new CoordinatedPhraseElement();
            Matcher prMatcher = coursePattern.matcher(pr);
            int count = 0;
            while(prMatcher.find()) {
                prereqsConj.addCoordinate(prMatcher.group(1).toUpperCase());
                count++;
            }
            if(count > 2) {
                prereqsConj.addPreModifier("all of");
            } else if(count == 2) {
                prereqsConj.addPreModifier("both");
            }
            prereqOptions.addCoordinate(prereqsConj);
        }
        if(prereqs.size() > 3) {
            prereqOptions.addCoordinate(nlgFactory.createNounPhrase((prereqs.size() - 3) + " more options"));
        }
        p.setObject(prereqOptions);
        return realiser.realiseSentence(p);
    }

    public static void main(String[] args) throws IOException {

        Lexicon lexicon = Lexicon.getDefaultLexicon();
        NLGFactory nlgFactory = new NLGFactory(lexicon);
        Realiser realiser = new Realiser(lexicon);

        Scanner in = new Scanner(System.in);
        System.out.print("Enter student ID: ");
        String studentid = in.nextLine().trim();
        while(!studentid.matches("^\\d{9}$")) {
            System.out.println("Invalid ID!");
            System.out.print("Enter student ID: ");
            studentid = in.nextLine().trim();
        }

        while(true) {
            System.out.print("Query: ");
            String input = in.nextLine().trim();
            Map<String, String> entities = null;
            System.out.println("=" + input + "=");
            if(input.isEmpty()) { break; }

            String query = null;
            String intent = null;
            String response = "I do not understand that question. Try saying 'What classes should I take next?' or 'What classes must I take to graduate?' or 'What are the prerequisites for CSCI141?'"; 
            try {
                JSONObject rasa_resp = Unirest.get("http://localhost:5000/parse")
                    .header("accept", "application/json")
                    .queryString("q", input)
                    .asJson()
                    .getBody()
                    .getObject();
                intent = rasa_resp.getJSONObject("intent").getString("name");
                double intent_conf = rasa_resp.getJSONObject("intent").getDouble("confidence");

                String course = null; // some intents extract a course from the input text

                HttpRequestWithBody tarotReq = 
                    Unirest.post("http://localhost:10333/tarot")
                           .header("content-type", "application/json; charset=utf-8")
                           .header("accept", "application/json");

                StringWriter reqBodyWriter = new StringWriter();
                JSONWriter reqBodyJSONWriter = new JSONWriter(reqBodyWriter).array();
                if(intent_conf > 0.90) {
                    if(intent.equals("schedule_finish_degree")) {
                        reqBodyJSONWriter.value("finishDegreeFromStudentId");
                        reqBodyJSONWriter.value(studentid);
                        reqBodyJSONWriter.value("[csci]");
                        reqBodyJSONWriter.value("4");
                        reqBodyJSONWriter.value("2018");
                        reqBodyJSONWriter.value("fall");
                        reqBodyJSONWriter.value("[fsem,jsem,csci141]");
                        reqBodyJSONWriter.value("Taken");
                        reqBodyJSONWriter.value("PlannedSemesters");
                        reqBodyJSONWriter.value("Gpa");
                        reqBodyJSONWriter.value("MinGpa");
                        reqBodyJSONWriter.value("MaxGpa");
                        reqBodyJSONWriter.value("CreditCount");
                        reqBodyJSONWriter.value("AllCreditCount");
                        reqBodyJSONWriter.value("PlannedCreditCount");
                        reqBodyJSONWriter.value("PlannedAllCreditCount");
                    }
                    else if(intent.equals("schedule_single_semester")) {
                        reqBodyJSONWriter.value("finishSingleSemesterFromStudentId");
                        reqBodyJSONWriter.value(studentid);
                        reqBodyJSONWriter.value("[csci]");
                        reqBodyJSONWriter.value("8");
                        reqBodyJSONWriter.value("2018");
                        reqBodyJSONWriter.value("fall");
                        reqBodyJSONWriter.value("[fsem,jsem,csci141]");
                        reqBodyJSONWriter.value("Taken");
                        reqBodyJSONWriter.value("PlannedSemesters");
                    }
                    else if(intent.equals("prereqs")) {
                        course = findCourseInText(input);
                        reqBodyJSONWriter.value("getPrereqs");
                        reqBodyJSONWriter.value(course);
                        reqBodyJSONWriter.value("Prereqs");
                    }
                    reqBodyJSONWriter.endArray();
                    System.out.println(reqBodyWriter.toString());
                    JSONArray tarot_resp = tarotReq.body(reqBodyWriter.toString())
                        .asJson().getBody().getArray();
                    System.out.println(tarot_resp);

                    if(intent.equals("schedule_finish_degree") ||
                            intent.equals("schedule_single_semester")) {
                        // get first answer
                        JSONObject answer = tarot_resp.getJSONObject(0);
                        String planned_semesters = answer.getString("PlannedSemesters");
                        System.out.println(planned_semesters);
                        response = respondPlannedSemesters(nlgFactory, realiser, planned_semesters);
                    }
                    else if(intent.equals("prereqs")) {
                        // get all answers
                        List<String> prereqs = new ArrayList<String>();
                        for(int i = 0; i < tarot_resp.length(); i++) {
                            prereqs.add(tarot_resp.getJSONObject(i).getString("Prereqs"));
                        }
                        System.out.println(prereqs);
                        response = respondPrereqs(nlgFactory, realiser, course, prereqs);
                    }
                }
                System.out.println("-> " + response);
            } catch(UnirestException e) {
                System.out.println(e);
                break;
            }
        }
        Unirest.shutdown();
    }
}


