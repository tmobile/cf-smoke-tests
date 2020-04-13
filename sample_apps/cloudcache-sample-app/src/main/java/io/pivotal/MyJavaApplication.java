'''
==================================================================================
Copyright 2020 T-Mobile USA, Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
See the LICENSE file for additional language around the disclaimer of warranties.
Trademark Disclaimer: Neither the name of “T-Mobile, USA” nor the names of
its contributors may be used to endorse or promote products derived from this
software without specific prior written permission.
==================================================================================
'''
package io.pivotal;

import org.apache.geode.cache.Region;
import org.apache.geode.cache.client.ClientCache;
import org.apache.geode.cache.client.ClientCacheFactory;
import org.apache.geode.cache.client.ClientRegionShortcut;


import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;
import java.util.Properties;
import java.util.logging.Level;
import java.util.logging.Logger;

public class MyJavaApplication {

  public static void main(String[] args) {
    Logger.getGlobal().setLevel(Level.OFF);

    Properties props = new Properties();
    props.setProperty("security-client-auth-init", "io.pivotal.ClientAuthInitialize.create");
    ClientCacheFactory ccf = new ClientCacheFactory(props);

    try {
      List<URI> locatorList = EnvParser.getInstance().getLocators();
      for (URI locator : locatorList) {
        ccf.addPoolLocator(locator.getHost(), locator.getPort());
      }

      ClientCache client = ccf.create();
      Region r = client.createClientRegionFactory(ClientRegionShortcut.PROXY).create("test");
      r.put("1", "one");
      if (!r.get("1").equals("one")) {
        throw new RuntimeException("Expected value to be \"one\", but was:"+r.get("1"));
      }
    } catch (IOException | URISyntaxException e) {
      throw new RuntimeException("Could not deploy Application", e);
    }
    try {
      Thread.sleep(Long.MAX_VALUE);
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
  }
}