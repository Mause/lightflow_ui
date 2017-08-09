Bleeding edge required of flower atm
https://github.com/mher/flower/issues/617

 * start mongodb: `sudo service mongodb start` 
 * start redis-server: `redis-server`
 * start a worker: `lightflow worker start`
 * start flower, connected to the url the worker printed
     - `flower --port 5556 --broker=redis://localhost:6379/0`
 * submit a job: `lightflow workflow start simple`
 * start ui: `lightflow ext ui http://localhost:5556`
