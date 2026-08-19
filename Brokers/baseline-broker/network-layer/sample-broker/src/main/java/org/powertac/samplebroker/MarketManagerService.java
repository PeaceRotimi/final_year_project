/*
 * Copyright (c) 2012-2014 by the original author
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.powertac.samplebroker;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

import org.apache.logging.log4j.Logger;
import org.apache.logging.log4j.LogManager;
import org.powertac.common.BalancingTransaction;
import org.powertac.common.CapacityTransaction;
import org.powertac.common.ClearedTrade;
import org.powertac.common.Competition;
import org.powertac.common.DistributionTransaction;
import org.powertac.common.MarketPosition;
import org.powertac.common.MarketTransaction;
import org.powertac.common.Order;
import org.powertac.common.Orderbook;
import org.powertac.common.Timeslot;
import org.powertac.common.WeatherForecast;
import org.powertac.common.WeatherReport;
import org.powertac.common.config.ConfigurableValue;
import org.powertac.common.msg.BalanceReport;
import org.powertac.common.msg.MarketBootstrapData;
import org.powertac.common.repo.TimeslotRepo;
import org.powertac.samplebroker.core.BrokerPropertiesService;
import org.powertac.samplebroker.interfaces.Activatable;
import org.powertac.samplebroker.interfaces.BrokerContext;
import org.powertac.samplebroker.interfaces.Initializable;
import org.powertac.samplebroker.interfaces.MarketManager;
import org.powertac.samplebroker.interfaces.PortfolioManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;


import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Handles market interactions on behalf of the broker.
 * @author John Collins
 * Modified by Oluwatoni Rotimi-Fabolude 2026
 */
@Service
public class MarketManagerService
implements MarketManager, Initializable, Activatable
{
  @Autowired
  private RedisBridge redisBridge;


  static private Logger log = LogManager.getLogger(MarketManagerService.class);


  private ObjectMapper mapper = new ObjectMapper();

  @Autowired
  private BrokerContext broker; // broker


  @Autowired
  private BrokerPropertiesService propertiesService;

  @Autowired
  private TimeslotRepo timeslotRepo;

  @Autowired
  private PortfolioManager portfolioManager;


  // ------------ Configurable parameters --------------
  // max and min offer prices. Max means "sure to trade"
  @ConfigurableValue(valueType = "Double",
          description = "Upper end (least negative) of bid price range")
  private double buyLimitPriceMax = -1.0;  // broker pays

  @ConfigurableValue(valueType = "Double",
          description = "Lower end (most negative) of bid price range")
  private double buyLimitPriceMin = -70.0;  // broker pays

  @ConfigurableValue(valueType = "Double",
          description = "Upper end (most positive) of ask price range")
  private double sellLimitPriceMax = 70.0;    // other broker pays

  @ConfigurableValue(valueType = "Double",
          description = "Lower end (least positive) of ask price range")
  private double sellLimitPriceMin = 0.5;    // other broker pays

  @ConfigurableValue(valueType = "Double",
          description = "Minimum bid/ask quantity in MWh")
  private double minMWh = 0.001; // don't worry about 1 KWh or less

  @ConfigurableValue(valueType = "Integer",
          description = "If set, seed the random generator")
  private Integer seedNumber = null;

  // ---------------- local state ------------------
  private Random randomGen; // to randomize bid/ask prices

  // Bid recording
  private HashMap<Integer, Order> lastOrder;
  private double[] marketMWh;
  private double[] marketPrice;
  private double meanMarketPrice = 0.0;

  public MarketManagerService ()
  {
    super();
  }

  /* (non-Javadoc)
   * @see org.powertac.samplebroker.MarketManager#init(org.powertac.samplebroker.SampleBroker)
   */
  @Override
  public void initialize (BrokerContext broker)
  {
    this.broker = broker;
    lastOrder = new HashMap<>();
    propertiesService.configureMe(this);
    System.out.println("  name=" + broker.getBrokerUsername());
    if (seedNumber != null) {
      System.out.println("  seeding=" + seedNumber);
      log.info("Seeding with : " + seedNumber);
      randomGen = new Random(seedNumber);
    }
    else {
      randomGen = new Random();
    }
  }

  // ----------------- data access -------------------
  /**
   * Returns the mean price observed in the market during the bootstrap session.
   */
  @Override
  public double getMeanMarketPrice ()
  {
    return meanMarketPrice;
  }

  // --------------- message handling -----------------
  /**
   * Handles the Competition instance that arrives at beginning of game.
   * Here we capture minimum order size to avoid running into the limit
   * and generating unhelpful error messages.
   */
  public synchronized void handleMessage (Competition comp)
  {
    // if(comp!=null){
    //   sendToRedis("game-state", comp);
    //   log.info("Published Competition info " );
    // }


  }

  /**
   * Handles a BalancingTransaction message.
   */
  public synchronized void handleMessage (BalancingTransaction tx)
  {

    if(tx != null){
      sendToRedis("game-state", tx);
      log.info("Published Balancing Transaction of "+ tx.getCharge() + "for" + tx.getKWh() + "kWh");
    }
  }

  /**
   * Handles a ClearedTrade message - this is where you would want to keep
   * track of market prices.
   */
  public synchronized void handleMessage (ClearedTrade ct)
  {
     if(ct !=null){
      sendToRedis("wholesale-market", ct);
      log.info("Published Cleared Trade message for timeslot:" + ct.getTimeslotIndex() + "for" + ct.getExecutionMWh() + "MWh for a price of " + ct.getExecutionPrice() );
    }

  }

  /**
   * Handles a DistributionTransaction - charges for transporting power
   */
  public synchronized void handleMessage (DistributionTransaction dt)
  {
     if(dt !=null){
      sendToRedis("bank-transaction", dt);
      log.info("Published Distribution Transaction of " + dt.getCharge() + " for " + dt.getKWh() + " kWh");
    }
  }

  /**
   * Handles a CapacityTransaction - a charge for contribution to overall
   * peak demand over the recent past.
   */
  public synchronized void handleMessage (CapacityTransaction dt)
  {
     if(dt !=null){
      sendToRedis("bank-transaction", dt);
      log.info("Published Capacity Transaction for " +  dt.getCharge() + "with a threshold of" + dt.getThreshold());
    }
  }

  /**
   * Receives a MarketBootstrapData message, reporting usage and prices
   * for the bootstrap period. We record the overall weighted mean price,
   * as well as the mean price and usage for a week.
   */
  public synchronized void handleMessage (MarketBootstrapData data)
  {
    // marketMWh = new double[broker.getUsageRecordLength()];
    // marketPrice = new double[broker.getUsageRecordLength()];
    // double totalUsage = 0.0;
    // double totalValue = 0.0;
    // for (int i = 0; i < data.getMwh().length; i++) {
    //   totalUsage += data.getMwh()[i];
    //   totalValue += data.getMarketPrice()[i] * data.getMwh()[i];
    //   if (i < broker.getUsageRecordLength()) {
    //     // first pass, just copy the data
    //     marketMWh[i] = data.getMwh()[i];
    //     marketPrice[i] = data.getMarketPrice()[i];
    //   }
    //   else {
    //     // subsequent passes, accumulate mean values
    //     int pass = i / broker.getUsageRecordLength();
    //     int index = i % broker.getUsageRecordLength();
    //     marketMWh[index] =
    //         (marketMWh[index] * pass + data.getMwh()[i]) / (pass + 1);
    //     marketPrice[index] =
    //         (marketPrice[index] * pass + data.getMarketPrice()[i]) / (pass + 1);
    //   }
    // }
    // meanMarketPrice = totalValue / totalUsage;

     if(data!=null){
      sendToRedis("game-state", data);
      log.info("Published Market Bootstrap Data ");
    }
  }

  /**
   * Receives a MarketPosition message, representing our commitments on
   * the wholesale market
   */
  public synchronized void handleMessage (MarketPosition posn)
  {

    if(posn!=null){
      sendToRedis("wholesale-market", posn);
      log.info("Published Market Position in Timeslot" + posn.getTimeslotIndex() + " and overall balance" + posn.getOverallBalance());
    }
  }

  /**
   * Receives a new MarketTransaction. We look to see whether an order we
   * have placed has cleared.
   */

  // Modified by Oluwatoni Rotimi-Fabolude
  public synchronized void handleMessage (MarketTransaction tx)
  {
    // convert transaction data to JSON and send it to Redis

    if(tx!=null){
      sendToRedis("wholesale-market", tx);
      log.info("Published Market Transaction Data for timeslot: "+ tx.getTimeslotIndex() + tx.getMWh() + " MWh at " + tx.getPrice());
    }

  }

  /**
   * Receives market orderbooks. These list un-cleared bids and asks,
   * from which a broker can construct approximate supply and demand curves
   * for the following timeslot.
   */
  public synchronized void handleMessage (Orderbook orderbook)
  {

    if(orderbook!=null){
      sendToRedis("wholesale-market", orderbook);
      log.info("Published Orderbook in timeslot: "+ orderbook.getTimeslotIndex() + " with a clearing price" + orderbook.getClearingPrice());
    }
  }

  /**
   * Receives a new WeatherForecast.
   */
  public synchronized void handleMessage (WeatherForecast forecast)
  {
    if(forecast !=null){
      sendToRedis("weather-report", forecast);
      log.info("Published Weather Forecasts for timeslot:" + forecast.getTimeslotIndex());
    }
  }

  /**
   * Receives a new WeatherReport.
   */

  public synchronized void handleMessage (WeatherReport report)
  {
    if(report !=null){
      sendToRedis("weather-report", report);
      log.info("Published WeatherReport for timeslot:" + report.getTimeslotIndex());
    }


  }

  /**
   * Receives a BalanceReport containing information about imbalance in the
   * current timeslot.
   */
  public synchronized void handleMessage (BalanceReport report)
  {
    if(report!=null){
      sendToRedis("wholesale-market", report);
      log.info("Published Balance Report for timeslot");
    }
  }

  // ----------- per-timeslot activation ---------------

  /**
   * Compute needed quantities for each open timeslot, then submit orders
   * for those quantities.
   *
   * @see org.powertac.samplebroker.interfaces.Activatable#activate(int)
   */
  @Override
  public synchronized void activate (int timeslotIndex)
  {
    double neededKWh = 0.0;
    log.debug("Current timeslot is " + timeslotRepo.currentTimeslot().getSerialNumber());
    for (Timeslot timeslot : timeslotRepo.enabledTimeslots()) {
      int index = (timeslot.getSerialNumber()) % broker.getUsageRecordLength();
      neededKWh = portfolioManager.collectUsage(index);
      // submitOrder(neededKWh, timeslot.getSerialNumber());
    }
  }

  /**
   * Composes and submits the appropriate order for the given timeslot.
   */
  private void submitOrder (double neededKWh, int timeslot)
  {
    double neededMWh = neededKWh / 1000.0;

    MarketPosition posn =
        broker.getBroker().findMarketPositionByTimeslot(timeslot);
    if (posn != null)
      neededMWh -= posn.getOverallBalance();
    if (Math.abs(neededMWh) <= minMWh) {
      log.info("no power required in timeslot " + timeslot);
      return;
    }
    Double limitPrice = computeLimitPrice(timeslot, neededMWh);
    log.info("new order for " + neededMWh + " at " + limitPrice +
             " in timeslot " + timeslot);
    Order order = new Order(broker.getBroker(), timeslot, neededMWh, limitPrice);
    lastOrder.put(timeslot, order);
    // broker.sendMessage(order);
  }

  /**
   * Computes a limit price with a random element.
   */
  private Double computeLimitPrice (int timeslot,
                                    double amountNeeded)
  {
    log.debug("Compute limit for " + amountNeeded +
              ", timeslot " + timeslot);
    // start with default limits
    Double oldLimitPrice;
    double minPrice;
    if (amountNeeded > 0.0) {
      // buying
      oldLimitPrice = buyLimitPriceMax;
      minPrice = buyLimitPriceMin;
    }
    else {
      // selling
      oldLimitPrice = sellLimitPriceMax;
      minPrice = sellLimitPriceMin;
    }
    // check for escalation
    Order lastTry = lastOrder.get(timeslot);
    if (lastTry != null)
      log.debug("lastTry: " + lastTry.getMWh() +
                " at " + lastTry.getLimitPrice());
    if (lastTry != null
        && Math.signum(amountNeeded) == Math.signum(lastTry.getMWh())) {
      oldLimitPrice = lastTry.getLimitPrice();
      log.debug("old limit price: " + oldLimitPrice);
    }

    // set price between oldLimitPrice and maxPrice, according to number of
    // remaining chances we have to get what we need.
    double newLimitPrice = minPrice; // default value
    int current = timeslotRepo.currentSerialNumber();
    int remainingTries = (timeslot - current
                          - Competition.currentCompetition().getDeactivateTimeslotsAhead());
    log.debug("remainingTries: " + remainingTries);
    if (remainingTries > 0) {
      double range = (minPrice - oldLimitPrice) * 2.0 / (double)remainingTries;
      log.debug("oldLimitPrice=" + oldLimitPrice + ", range=" + range);
      double computedPrice = oldLimitPrice + randomGen.nextDouble() * range;
      return Math.max(newLimitPrice, computedPrice);
    }
    else
      return null; // market order
  }


  private void sendToRedis(String channel, Object data) {
      try {
          String json = mapper.writeValueAsString(data);
          redisBridge.publish(channel, json);
      } catch (Exception e) {
          log.error("Failed to convert data to JSON for channel: " + channel, e);
      }
  }
}
