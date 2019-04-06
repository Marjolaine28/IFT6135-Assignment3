import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import SGD
import numpy as np
import matplotlib.pyplot as plt
import samplers
import argparse

class Classifier(nn.Module):
    def __init__(self, input_size):
        super(Classifier, self).__init__()
        self.input_size = input_size
        
        self.layer1 = nn.Linear(self.input_size, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, 1)
        
    def forward(self, x):
        out = F.relu(self.layer1(x))
        out = F.relu(self.layer2(out))
        out = F.sigmoid(self.layer3(out))
        return out
    
def train(metric, dist1, dist2, use_cuda=False):
    D = Classifier(2)
    if use_cuda:
        D.cuda()
    optimizer = SGD(D.parameters(), lr=0.001)
    
    for it in range(10000):
        optimizer.zero_grad()
        x_1 = torch.from_numpy(next(dist1)).float()
        x_2 = torch.from_numpy(next(dist2)).float()
        if use_cuda:
            x_1 = x_1.cuda()
            x_2 = x_2.cuda()
        y_1 = D(x_1)
        y_2 = D(x_2)
        
        if metric == 'JSD':
            loss = - torch.mean(torch.log(y_1)) - torch.mean(torch.log(1 - y_2))
            
        loss.backward()
        optimizer.step()
        
    return D
    
def estimate(metric, dist1, dist2, D, use_cuda=False):
    x_1 = torch.from_numpy(next(dist1)).float()
    x_2 = torch.from_numpy(next(dist2)).float()
    if use_cuda:
        x_1 = x_1.cuda()
        x_2 = x_2.cuda()
    y_1 = D(x_1)
    y_2 = D(x_2)
    
    if metric == 'JSD':
        return np.log(2) + (0.5*torch.mean(torch.log(y_1)) + 0.5*torch.mean(torch.log(1 - y_2))).data.cpu().numpy()
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--metric', type=str, default='JSD', help="options are 'WS' or 'JSD'")
    parser.add_argument('--use_cuda', type=bool, default=False)
    parser.add_argument('--setup', type=int, default=1)
    args = parser.parse_args()
    
    if args.setup == 1:
        data_points = ([],[])
        dist1 = samplers.distribution1(0, batch_size=512)
        for x in np.arange(-1.0, 1.01, 0.1):
            x = np.around(x, decimals=1)
            print("x = " + str(x))
            dist2 = samplers.distribution1(x, batch_size=512)
            D = train(args.metric, dist1, dist2, args.use_cuda)
            y = estimate(args.metric, dist1, dist2, D, args.use_cuda)
            data_points[0].append(x)
            data_points[1].append(y)
            
        plt.plot(data_points[0], data_points[1], '.')
        plt.show()