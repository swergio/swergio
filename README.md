# Swergio

Python package to enable and simplify communication between independent ML components via WebSocket.

Full documentation for the swergio project can be found at https://swergio.github.io.

## Motivation

We are all aware that every machine learning and data science model is just a part of a whole process, the price prediction model, which is later used to control the buying of raw materials, or the customer churn model, which leads to different actions towards customers. Our models are using prepared data and the predictions are consumed by following business processes or even other models, which can make the end-to-end process quite large and complex. 

In general, we’re trying to reduce such complexity by focusing only on the model part. We will use prepared training data and optimize our model to fit an intermediate or approximate goal, e.g., forecast error or accuracy.

![](imgs/train.png)

For model inference we usually integrate the trained model into a given process, receiving live data for the model and sending the model prediction further down the process.

![](imgs/inference.png)

Also, this approach simplifies the complexity of our data science projects and is often good enough to reach useful results, but it still has a few challenges we need to overcome:

- What is the appropriate goal we should aim for? E.g., is model accuracy the best measure for the overall process outcome?
- How to incorporate live feedback into the process and how to adjust the model based on live feedback?
- In what way can we reuse learned models to optimize and control the input parameters of the process?
- How to effectively monitor the model’s performance?

The challenges are mostly tackled by adding additional complexity to our process e.g., entirely separate components and code to handle feedback, etc. 

A more straightforward approach is to enable a direct feedback mechanism into our forward process, that allows our models and components to get more information on how well their performance is down the line. 

![](imgs/swergio.png)

Such a mechanism allows us to be used in several settings and scenarios:

- Train our model directly based on a goal down the process (e.g., differentiable programming Trebuchet example) 
- Collect live reward feedback from an environment to train an RL model (RL example)
- Gather live human feedback to label uncertain data in an active learning approach (Music Generator example)
- Optimize the input of our process using gradient-based optimization technics (control problems)  

The swergio package helps us to implement and enable forward and backward communication between independent components.

To ensure the independence between the components and not require that all components are aware of each other, communication is implemented via Web Sockets and each component is only aware of certain communication rooms. The components can send and handle incoming messages. 


## How to install

To install the swergio package directly from Pypi:

```
pip install swergio 
```

For the latest version from github we can use:

```
pip install swergio !!!!!!!
```

If we want to install swergio including the toolbox package with useful functionalities we can do this from Pypi using:

```
pip install swergio[toolbox] 
```


## First steps

In the examples repository (https://github.com/swergio/Examples) we find a "Hello world" example for the swergio package, which shows th basic usage of starting a websocket server and having two clients communicating via message.

A more detailed description of this example can be found in the documentation (https://swergio.github.io)


## Related resources

- Julia package for swergio client (https://github.com/swergio/swergio.jl)
- Toolbox of useful functions and methods to extend the swergio capabilities (https://github.com/swergio/swergio_toolbox)
- Use case examples (https://github.com/swergio/Examples)
    - Control a trebuchet via neural network
    - Continuos evolution of policy models in reinforcement learning
    - Generate melodies using genetic algorithm paired with active learning to provide quicker feedback
