/*
 * Copyright (c) 2012 by the original author
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

import org.apache.logging.log4j.Logger;
import org.apache.logging.log4j.LogManager;
import org.powertac.common.BankTransaction;
import org.powertac.common.CashPosition;
import org.powertac.common.Competition;
import org.powertac.common.msg.DistributionReport;
import org.powertac.samplebroker.core.BrokerPropertiesService;
import org.powertac.samplebroker.interfaces.BrokerContext;
import org.powertac.samplebroker.interfaces.Initializable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.databind.ObjectMapper;
/**
 * Handles incoming context and bank messages with example behaviors.
 * @author John Collins
 */
@Service
public class ContextManagerService
implements Initializable
{
  static private Logger log = LogManager.getLogger(ContextManagerService.class);

  @Autowired
  private BrokerPropertiesService propertiesService;

  @Autowired
  private RedisBridge redisBridge;


  private ObjectMapper mapper = new ObjectMapper();

  BrokerContext master;

  // current cash balance
  private double cash = 0;


//  @SuppressWarnings("unchecked")
  @Override
  public void initialize (BrokerContext broker)
  {
    master = broker;
    propertiesService.configureMe(this);
// --- no longer needed ---
//    for (Class<?> clazz: Arrays.asList(BankTransaction.class,
//                                       CashPosition.class,
//                                       DistributionReport.class,
//                                       Competition.class,
//                                       java.util.Properties.class)) {
//      broker.registerMessageHandler(this, clazz);
//    }
  }

  // -------------------- message handlers ---------------------
  //
  // Note that these arrive in JMS threads; If they share data with the
  // agent processing thread, they need to be synchronized.

  /**
   * BankTransaction represents an interest payment. Value is positive for
   * credit, negative for debit.
   */
  public void handleMessage (BankTransaction btx)
  {
    if(btx != null){
      sendToRedis("bank-transactions", btx);
      log.info("Published Bank Transaction: " + btx.getAmount());
    }

  }

  /**
   * CashPosition updates our current bank balance.
   */
  public void handleMessage (CashPosition cp)
  {
    if (cp != null) {
      sendToRedis("bank-transactions", cp);
      log.info("Published Cash Position: current balance -" + cp.getBalance());
    }
  }

  /**
   * DistributionReport gives total consumption and production for the timeslot,
   * summed across all brokers.
   */
  public void handleMessage (DistributionReport dr)
  {
    if (dr != null) {
      sendToRedis("wholesale-market", dr);
      log.info("Published Distribution Report - Timeslot " + dr.getTimeslot() + " total consumption=" + dr.getTotalConsumption() + ", total production=" + dr.getTotalProduction());
    }
  }

  /**
   * Handles the Competition instance that arrives at beginning of game.
   * Here we capture all the customer records so we can keep track of their
   * subscriptions and usage profiles.
   */
  public void handleMessage (Competition comp)
  {
    if (comp != null) {
      sendToRedis("game-state", comp);
      log.info("Published Competition info: " + comp.getName());
    }
  }

  /**
   * Receives the server configuration properties.
   */
  public void handleMessage (java.util.Properties serverProps)
  {
    if (serverProps != null) {
      sendToRedis("game-state", serverProps);
      log.info("Published Server Properties: " + serverProps.size() + " config rules received");
    }

  }

  /**
   * Helper method to safely convert objects to JSON and send to Redis
   */
  private void sendToRedis(String channel, Object data) {
      try {
          String json = mapper.writeValueAsString(data);
          redisBridge.publish(channel, json);
      } catch (Exception e) {
          log.error("Failed to convert data to JSON for channel: " + channel, e);
      }
  }

}
