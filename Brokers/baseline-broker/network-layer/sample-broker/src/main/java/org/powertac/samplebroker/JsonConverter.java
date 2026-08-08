package org.powertac.samplebroker;

import com.google.gson.Gson;

/**
 *
 * A class converting the Power TAC Server Objects to JSON strings.
 *
*@author Oluwatoni Rotimi-Fabolude
*
*/




public class JsonConverter {

    private Gson gson;

    public JsonConverter(){

        this.gson = new Gson();

    }
 // takes Power TAC object and turns it to JSON string
    public String toJson(Object powerTacObject){
        return gson.toJson(powerTacObject);
    }

}
