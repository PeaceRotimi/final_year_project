package org.powertac.samplebroker;

import org.junit.jupiter.api.Test;
import org.powertac.common.WeatherReport;

import static org.junit.jupiter.api.Assertions.*;

import java.beans.Transient;

/**
 * Test cases for converting Power TAC Messages.
 *
 * @author Oluwatoni Rotimi-Fabolude
 */
public class JsonConverterTest {

    @Test

    public void testWeatherReportConvertsToJson(){
        // Arranage: Dummy weather report

        WeatherReport report = new WeatherReport(10,15.0,3.0,90.0,0.5);
        JsonConverter converter = new JsonConverter();

        // Act: Convert report

        String jsonResult = converter.toJson(report);

        System.out.println("ACTUAL JSON GENERATED: " + jsonResult);

        // Assert : Check that the result is not null and is in the right structure

        assertNotNull(jsonResult, "The JSON string should not be null.");

        boolean timeTrue = jsonResult.contains("\"currentTimeslot\":10");
        boolean tempTrue = jsonResult.contains("\"temperature\":15.0");
        boolean speedTrue = jsonResult.contains("\"windSpeed\":3.0");
        boolean dirTrue = jsonResult.contains("\"windDirection\":90.0");
        boolean cloudTrue = jsonResult.contains("\"cloudCover\":0.5");

        assertEquals(true, timeTrue, "JSON should contain the timeslot.");
        assertEquals(true, tempTrue, "JSON should contain the temperature.");
        assertEquals(true, speedTrue, "JSON should contain the wind speed.");
        assertEquals(true, dirTrue, "JSON should contain the wind direction.");
        assertEquals(true, cloudTrue, "JSON should contain the cloud cover.");


    }


}
