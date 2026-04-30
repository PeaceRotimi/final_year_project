import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.powertac.samplebroker.interfaces.BrokerContext;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Polls Redis for orders
 * @authour Oluwatoni Rotimi-Fabolude
 *
 */

@Service

public class OrderPoll{
    @Autowired
    private StringRedisTemplate redisTemplate;

    @Autowired
    private BrokerContext brokerContext;

    @Scheduled(fixedRate = 500)
    public void checkForOrders(){
        String orders = redisTemplate.opsForList().leftPop("action_queue");

        if (orders != null){
            parseAndSubmit(orders);
        }
    }

    private void parseAndSubmit(String json){

        try{
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(json);

            int timeslot = root.get("timeslot").asInt();
            double amount = root.get("energy_amount").asDouble();
            double price = root.get("limit_price").asDouble();

            System.out.println("[Bridge] Order : Type=" + (amount > 0 ? "BUY" : "SELL") + ",MWh=" + amount + ", Price=" + price);

        } catch (Exception e) {
        System.err.println("[BRIDGE] Error parsing JSON order: " + e.getMessage());
    }
        }
    }
