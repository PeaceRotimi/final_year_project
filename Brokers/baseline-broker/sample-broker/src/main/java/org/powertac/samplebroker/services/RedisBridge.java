package org.powertac.samplebroker.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.powertac.samplebroker.interfaces.BrokerContext;
import org.powertac.common.repo.TimeslotRepo;
import org.powertac.common.repo.TariffRepo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import org.powertac.common.Order;
import org.powertac.common.Timeslot;
import org.powertac.common.Competition;
import org.powertac.common.TariffSpecification;
import org.powertac.common.Rate;
import org.powertac.common.enumerations.PowerType;
import org.powertac.common.msg.TariffRevoke;
import org.powertac.common.msg.EconomicControlEvent;

/**
 * bridging data between the Power TAC Broker and Redis
 * @author Oluwatoni Rotimi-Fabolude
 */
@Service
public class RedisBridge implements MessageListener {

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Autowired
    private BrokerContext brokerContext;

    @Autowired
    private TimeslotRepo timeslotRepo;

    @Autowired
    private TariffRepo tariffRepo;

    private ObjectMapper mapper = new ObjectMapper();

    private Competition simContext = null;

    public void sendToPython(String channel, String message){
        Competition comp = Competition.currentCompetition();
        if (comp != null) {
            this.simContext = comp;
        }

        try {
            redisTemplate.convertAndSend(channel, message);
        } catch (Exception e) {
            System.err.println("ERROR: Failed to send message to Redis. " + e.getMessage());
        }
    }

    @Override
    public void onMessage(Message message, byte[] pattern){
        String channel = new String(message.getChannel());
        String body = new String(message.getBody());


        if(channel.equals("broker_commands")){
            executeCommand(body);
        }
    }

    private void executeCommand(String jsonCommand){
        try {

            if (this.simContext == null) {
                System.err.println("IGNORED: Command received before game context was captured.");
                return;
            }
            Competition.setCurrent(this.simContext);

            JsonNode command = mapper.readTree(jsonCommand);
            String action = command.get("action").asText().trim();
            System.out.println(" Python Command: [" + action + "]");


            if (action.equals("BUY")) {
                int tsIndex = command.get("timeslot").asInt();
                double mwh = command.get("mwh").asDouble();

                Double limitPrice = null;
                if (command.hasNonNull("limitPrice")) {
                    limitPrice = command.get("limitPrice").asDouble();
                }

                Timeslot targetTimeslot = timeslotRepo.findBySerialNumber(tsIndex);

                if (targetTimeslot != null) {
                    Order order = new Order(brokerContext.getBroker(), targetTimeslot, mwh, limitPrice);
                    brokerContext.sendMessage(order);
                    System.out.println(" wholesale - Ordered " + mwh + " MWh for TS " + tsIndex);
                }
                return;
            }


            if (action.equals("REVOKE_TARIFF")) {
                long oldId = command.get("tariffId").asLong();
                TariffSpecification oldSpec = tariffRepo.findSpecificationById(oldId);
                if (oldSpec != null) {
                    TariffRevoke revoke = new TariffRevoke(brokerContext.getBroker(), oldSpec);
                    brokerContext.sendMessage(revoke);
                    System.out.println("RETAIL: Revoked tariff " + oldId);
                }
                return;
            }


            PowerType pt = PowerType.valueOf(command.get("powerType").asText());
            double rateValue = command.get("rateValue").asDouble();
            double periodicPayment = command.get("periodicPayment").asDouble();

            TariffSpecification spec = new TariffSpecification(brokerContext.getBroker(), pt).withPeriodicPayment(periodicPayment);
            Rate rate = new Rate().withValue(rateValue);
            spec.addRate(rate);

            if (action.equals("SUPERSEDE") && command.hasNonNull("supersedesId")) {
                long oldId = command.get("supersedesId").asLong();
                spec.addSupersedes(oldId);

                TariffSpecification oldSpec = tariffRepo.findSpecificationById(oldId);
                if (oldSpec != null) {
                    TariffRevoke revoke = new TariffRevoke(brokerContext.getBroker(), oldSpec);
                    brokerContext.sendMessage(revoke);
                }
            }

            tariffRepo.addSpecification(spec);
            brokerContext.sendMessage(spec);

            System.out.println(" RETAIL- " + action + " successful. New Tariff ID: " + spec.getId());

        } catch (Exception e) {
            System.err.println(" Failed to process command from Python: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
