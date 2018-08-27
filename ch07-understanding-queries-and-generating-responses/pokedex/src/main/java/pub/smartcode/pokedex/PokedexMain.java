
package pub.smartcode.pokedex;

import alice.tuprolog.*;
import simplenlg.framework.*;
import simplenlg.lexicon.*;
import simplenlg.realiser.english.*;
import simplenlg.phrasespec.*;
import simplenlg.features.*;
import org.apache.commons.lang3.StringUtils;
import com.mashape.unirest.http.*;
import com.mashape.unirest.http.exceptions.*;
import org.json.*;
import java.util.*;
import java.io.*;

public class PokedexMain {
    public static String respond_can_breed_with(NLGFactory nlgFactory, Realiser realiser,
                                                Map<String, String> entities,
                                                List<Map<String, String>> varMaps) {
        SPhraseSpec p = nlgFactory.createClause();
        p.setSubject(StringUtils.capitalize(entities.get("pokemon")));
        p.setVerb("breed");
        p.setFeature(Feature.MODAL, "can");
        
        PPPhraseSpec prep_1 = nlgFactory.createPrepositionPhrase();
        prep_1.setPreposition("with");
        if(varMaps.size() > 1) {
            NPPhraseSpec object_1 = nlgFactory.createNounPhrase();
            object_1.setNoun(StringUtils.capitalize(varMaps.get(0).get("X")));
            NPPhraseSpec object_2 = nlgFactory.createNounPhrase();
            object_2.setNoun(StringUtils.capitalize(varMaps.get(1).get("X")));
            CoordinatedPhraseElement coord_obj =
                nlgFactory.createCoordinatedPhrase(object_1, object_2);
            if(varMaps.size() > 2) {
                NPPhraseSpec object_n = nlgFactory.createNounPhrase();
                object_n.setNoun((varMaps.size() - 2) + " more");
                coord_obj.addCoordinate(object_n);
            }
            coord_obj.setFeature(Feature.CONJUNCTION, "and");
            prep_1.addComplement(coord_obj);
        } else {
            NPPhraseSpec object_1 = nlgFactory.createNounPhrase();
            object_1.setNoun(StringUtils.capitalize(varMaps.get(0).get("X")));
            prep_1.addComplement(object_1);
        }
        p.setObject(prep_1);
        return realiser.realiseSentence(p);
    }

    public static String respond_child_pok(NLGFactory nlgFactory, Realiser realiser,
                                           Map<String, String> entities,
                                           List<Map<String, String>> varMaps) {
        SPhraseSpec p = nlgFactory.createClause();
        NPPhraseSpec subject_1 = nlgFactory.createNounPhrase();
        subject_1.setNoun(StringUtils.capitalize(entities.get("pokemon")));
        NPPhraseSpec subject_2 = nlgFactory.createNounPhrase();
        subject_2.setNoun(StringUtils.capitalize(entities.get("pokemon2")));
        CoordinatedPhraseElement coord_obj =
            nlgFactory.createCoordinatedPhrase(subject_1, subject_2);
        PPPhraseSpec prep_1 = nlgFactory.createPrepositionPhrase();
        prep_1.setPreposition("of");
        prep_1.addComplement(coord_obj);
        NPPhraseSpec child = nlgFactory.createNounPhrase("the", "child");
        p.setSubject(child);
        p.addPreModifier(prep_1);
        p.setVerb("is");
        p.setObject(StringUtils.capitalize(varMaps.get(0).get("X")));
        return realiser.realiseSentence(p);
    }

    public static void main(String[] args) throws IOException {
        if(args.length != 1) {
            System.out.println("Provide pokedex.pl path on command line.");
            return;
        }

        Scanner in = new Scanner(System.in);

        Prolog engine = new Prolog();
        try {
            engine.setTheory(new Theory(new FileInputStream(args[0])));
        } catch(InvalidTheoryException e) {
            System.out.println("Bad pokedex.pl: " + e);
            return;
        }

        Lexicon lexicon = Lexicon.getDefaultLexicon();
        NLGFactory nlgFactory = new NLGFactory(lexicon);
        Realiser realiser = new Realiser(lexicon);

        while(true) {
            System.out.print("Query: ");
            String input = in.nextLine().trim();
            Map<String, String> entities = null;
            System.out.println("=" + input + "=");
            if(input.isEmpty()) { break; }

            String query = null;
            String intent = null;
            try {
                JSONObject resp = Unirest.get("http://localhost:5000/parse")
                    .header("accept", "application/json")
                    .queryString("q", input)
                    .asJson()
                    .getBody()
                    .getObject();
                intent = resp.getJSONObject("intent").getString("name");
                double intent_conf = resp.getJSONObject("intent").getDouble("confidence");
                JSONArray entities_json = resp.getJSONArray("entities");
                System.out.println(intent + ": " + intent_conf);
                entities = new HashMap<String, String>();
                for(int i = 0; i < entities_json.length(); i++) {
                    // Here we prevent "Prolog-injection" (like SQL-injection) by ensuring
                    // there are no symbols in the entity values
                    String entity = entities_json.getJSONObject(i).getString("entity");
                    String value = entities_json.getJSONObject(i).getString("value");
                    if(value.matches("^[A-Za-z]+$")) {
                        entities.put(entity, value);
                    }
                }
                System.out.println(entities);
                if(intent_conf > 0.90 && entities_json.length() > 0) {
                    if(intent.equals("can_breed_with") && entities.containsKey("pokemon")) {
                        query = "can_breed(" + entities.get("pokemon").toLowerCase() + ", X).";
                    }
                    else if(intent.equals("can_breed") && entities.containsKey("pokemon") &&
                            entities.containsKey("pokemon2")) {
                        query = "can_breed(" + entities.get("pokemon").toLowerCase() + ", " +
                            entities.get("pokemon2").toLowerCase() + ").";
                    }
                    else if(intent.equals("child_pok") && entities.containsKey("pokemon") &&
                            entities.containsKey("pokemon2")) {
                        query = "child_pok(" + entities.get("pokemon").toLowerCase() + ", " +
                            entities.get("pokemon2").toLowerCase() + ", X)."; 
                    }
                }
            } catch(UnirestException e) {
                System.out.println(e);
                break;
            }
            String response = "I do not understand that question. Try asking 'Can X and Y breed?' or 'What can X breed with?' or 'What is the child of X and Y?'";
            if(query != null) {
                System.out.println(query);
                try {
                    SolveInfo result = engine.solve(query);
                    if(result.isHalted()) {
                        System.out.println("Error.");
                        break;
                    } else if(!result.isSuccess()) {
                        if(intent.equals("can_breed_with")) {
                            response = StringUtils.capitalize(entities.get("pokemon")) + 
                               " cannot breed with any others.";
                        }
                        else if(intent.equals("can_breed")) {
                            response = StringUtils.capitalize(entities.get("pokemon")) +
                                " cannot breed with " +
                                StringUtils.capitalize(entities.get("pokemon2"));
                        }
                        else if(intent.equals("child_pok")) {
                            response = "Sorry, I cannot determine the child species of " +
                                StringUtils.capitalize(entities.get("pokemon")) + " and " +
                                StringUtils.capitalize(entities.get("pokemon2")) + ".";
                        }
                    } else {
                        System.out.println(result);
                        List<Map<String, String>> varMaps = new ArrayList<Map<String, String>>();
                        do {
                            Map<String, String> varMap = new HashMap<String, String>();
                            System.out.println(result);
                            if(!result.isSuccess()) { break; }
                            for(Var var : result.getBindingVars()) {
                                varMap.put(var.getName(), 
                                        result.getVarValue(var.getName()).toString());
                                System.out.println(varMap);
                            }
                            varMaps.add(varMap);
                            result = engine.solveNext();
                        } while(result.hasOpenAlternatives());

                        System.out.println(varMaps);
                        try {
                            if(intent.equals("can_breed_with")) {
                                response = respond_can_breed_with(nlgFactory, realiser, entities, varMaps);
                            }
                            else if(intent.equals("can_breed")) {
                                response = "Yup!";
                            }
                            else if(intent.equals("child_pok")) {
                                response = respond_child_pok(nlgFactory, realiser, entities, varMaps);
                            }
                        } catch(Exception e) {
                            System.out.println("Error generating response.");
                            e.printStackTrace();
                        }
                    }
                } catch(NoMoreSolutionException e) {
                    System.out.println("No more solutions: " + e);
                    break;
                } catch(NoSolutionException e) {
                    System.out.println("No solution: " + e);
                    break;
                } catch(MalformedGoalException e) {
                    System.out.println("Error in goal: " + e);
                    break;
                }
            }
            System.out.println("-> " + response);
        }
        Unirest.shutdown();
    }
}


