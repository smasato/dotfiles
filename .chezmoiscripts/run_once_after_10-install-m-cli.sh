#!/bin/bash

# dock
m dock prune

# finder
m finder showhiddenfiles YES
m finder showextensions YES
m finder showdesktop NO 
m finder showpath YES

# timezone
m timezone set Asia/Tokyo
