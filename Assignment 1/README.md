# Hamster Network Database

This notebook analyzes the friendships and familylinks between users of the website hamsterster.com

**Data format (.edges):** source hamster, destination hamster

Source: https://networkrepository.com/petster-hamster.php

## Notes:
- Each node represents a pet profile on Hamsterster. 
- Each edge represents a friendship or family connection between two profiles.
- The number of relationships is given by the length of the dataset, since each line is a family connection or friendship. 
- The total number of relationships in the network equals the number of edges in the dataset.
- Relationships between profiles are undirected and unweighted.