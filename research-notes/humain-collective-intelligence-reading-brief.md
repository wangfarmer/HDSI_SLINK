# HUMA.I.N collective intelligence reading brief

This brief summarizes the MIT-linked readings shared for designing HUMA.I.N's collaboration scoring framework and S-Link composition. It is written as a working interpretation, not a final product spec.

## Executive synthesis

The readings converge on one product thesis:

> Collaboration potential is not the same as individual excellence. It is an emergent property of task design, group composition, interaction quality, motivation, feedback, and network structure.

For HUMA.I.N, this suggests that HUM should act less like a judge that ranks people once and more like a collaboration steward that:

1. Understands the collaboration "genome" of each task: what is being done, who can contribute, why they will contribute, and how contributions should be combined.
2. Scores observable collaboration behaviors, not only static credentials.
3. Designs S-Links as adaptive networks that refresh based on feedback, context, and changing group performance.
4. Uses AI mainly to structure discovery, synthesis, reflection, matching, and learning loops; it should be cautious about making hard human decisions on its own.
5. Balances engagement inside a group with exploration outside the group so teams do not become echo chambers.

## 1. Malone, Laubacher, and Dellarocas - "The Collective Intelligence Genome"

### Core idea

Collective intelligence systems can be designed as combinations of "genes." The authors organize these genes around four design questions:

- What is being done? Usually create, decide, or a combination of both.
- Who is doing it? A hierarchy, a crowd, or some hybrid.
- Why are they participating? Money, love/intrinsic motivation, glory/reputation, or a mix.
- How are contributions combined? Collection, collaboration, voting, consensus, averaging, prediction markets, hierarchy, etc.

The practical lesson is that collective intelligence is not magic. It is an organizational design problem.

### HUMA.I.N implications

- S-Links should be composed around the task genome, not around generic similarity alone.
- Different tasks require different collaboration patterns:
  - Creative ideation may need broad crowd input, exploration, and later selection.
  - Execution may need tighter collaboration, clear dependency management, and role clarity.
  - Judgment tasks may need independent estimates before social influence is introduced.
  - Consensus tasks need enough shared commitment and trust to bind people to a common result.
- Motivation should be explicit in the score. A person can be highly capable but poorly matched if their reason to participate does not fit the task.

### Design questions for HUMA.I.N

- For each S-Link, can HUM identify the task as create, decide, learn, coordinate, validate, or synthesize?
- Does the S-Link need independent contributions, tightly coupled collaboration, or staged create-then-decide?
- What incentive profile matters most: purpose, learning, reputation, money, belonging, reciprocity, or status?
- What aggregation rule is appropriate: expert review, group vote, consensus, weighted confidence, peer validation, or iterative synthesis?

## 2. Woolley, Chabris, Pentland, Hashmi, and Malone - "Evidence for a collective intelligence factor in the performance of human groups"

### Core idea

Groups appear to have a measurable collective intelligence factor, often called "c," analogous to individual general intelligence. In two studies with 699 people in groups of two to five, group performance across diverse tasks was predicted less by the highest or average individual IQ and more by interaction properties.

Key correlates included:

- Average social sensitivity of group members.
- Equality of conversational turn-taking.
- Lower domination by a few voices.
- Group composition factors that may proxy for social sensitivity, though HUMA.I.N should not use protected demographic traits as scoring shortcuts.

### HUMA.I.N implications

HUMA.I.N should not only score resumes, credentials, seniority, or individual expertise. It should also score:

- Whether people invite others into the conversation.
- Whether they listen and respond accurately.
- Whether they distribute airtime and decision influence.
- Whether they build on others' ideas instead of only broadcasting their own.
- Whether they improve group output across task types.

### Possible scoring dimensions

- Turn-taking balance: Does one person dominate, or is participation distributed?
- Responsiveness: Does a user reply to the substance of others' contributions?
- Social sensitivity: Does the user detect confusion, disagreement, uncertainty, or exclusion?
- Contribution uptake: Are the user's contributions used by others?
- Group lift: Do groups including this user improve in quality, speed, or alignment?

Important caution: these should be measured from behavior and outcomes, not inferred from demographics.

## 3. Vaccaro, Almaatouq, and Malone - "When combinations of humans and AI are useful"

### Core idea

The meta-analysis reviewed 106 experiments and 370 effect sizes comparing humans alone, AI alone, and human-AI combinations. The central warning is that human plus AI is not automatically better. On average, human-AI combinations underperformed the better of humans alone or AI alone. The pattern was especially weak for decision tasks, while creative or generative tasks showed more promise.

### HUMA.I.N implications

HUM should not be designed as a black-box authority that "scores people" and makes definitive collaboration decisions. The more suitable role is to help humans collaborate better by:

- Structuring search and discovery.
- Surfacing complementary collaborators.
- Prompting reflection before decisions.
- Summarizing multiple viewpoints.
- Helping groups separate independent ideation from group convergence.
- Making uncertainty visible.
- Testing whether AI assistance is actually improving outcomes.

### Product guardrails

- Treat AI recommendations as hypotheses to validate, not final truth.
- Separate "assistive scoring" from "authoritative judgment."
- Track whether HUM improves group outcomes versus human-only baselines.
- Be especially careful when AI is used for selection, ranking, exclusion, hiring, funding, or access decisions.
- Prefer AI support for creative/generative/synthesis workflows before high-stakes decision automation.

## 4. Almaatouq et al. - "Adaptive Social Networks Promote the Wisdom of Crowds"

### Core idea

Social networks are not static. In experiments and simulations, adaptive networks with feedback and plasticity produced more accurate collective estimates, sometimes outperforming the best individual member. The paper highlights two mechanisms:

- Global adaptation: the network changes its edges so better-performing members become more influential.
- Local adaptation: more accurate individuals become more resistant to social influence, so their initial judgments carry more weight.

### HUMA.I.N implications

This is highly relevant to S-Links. S-Links should refresh, decay, strengthen, or reconfigure based on observed behavior and feedback. Static matching will miss the central finding: collective intelligence improves when networks learn.

### S-Link design principles

- Links should have weights, confidence, and context, not just binary connected/not connected states.
- Links should decay if they are stale or not producing value.
- Links should strengthen when collaboration repeatedly improves outcomes.
- HUM should distinguish between task-specific reliability and global status. Someone may be excellent for one task and weak for another.
- Feedback should affect both node attributes (user collaboration profile) and edge attributes (pair or group relationship quality).
- Network adaptation should preserve diversity and avoid simply amplifying already central actors.

## 5. Pentland - "The New Science of Building Great Teams" and social physics

### Core idea

Pentland's work emphasizes that team performance is strongly shaped by communication patterns. Three concepts matter:

- Energy: the amount and intensity of communication among people.
- Engagement: how evenly that communication is distributed within a team.
- Exploration: how much team members seek information and ideas outside the team.

High-performing teams tend to have high energy, balanced engagement, and enough exploration to bring in new information. Exploration and engagement compete for limited attention, so effective systems often cycle between them.

### HUMA.I.N implications

HUMA.I.N's collaboration score should include network behavior:

- Is the user active enough to create momentum?
- Does the user engage broadly or only with a narrow clique?
- Does the user bridge to outside perspectives?
- Does the group have enough internal engagement to synthesize?
- Is the group over-exploring without converging, or over-engaged and becoming insular?

### S-Link implications

- In discovery phases, S-Links should favor exploration and weak ties.
- In synthesis/execution phases, S-Links should favor engagement, trust, and tighter coordination.
- HUM can help diagnose whether a group needs more outside input, more internal alignment, or better turn-taking.

## 6. Pentland - "Beyond the Echo Chamber"

### Core idea

Good decision-making depends on social exploration: continually engaging with diverse information sources. Echo chambers reduce decision quality because they limit information diversity and reinforce existing beliefs.

### HUMA.I.N implications

S-Link composition should not optimize only for affinity, shared background, or predicted agreement. It should intentionally include productive difference.

Possible measures:

- Information diversity of a user's network.
- Bridge role between otherwise disconnected groups.
- Exposure to dissenting or complementary viewpoints.
- Repeated ability to bring outside insight back into the group.

Guardrail: diversity should be treated as cognitive, experiential, professional, geographic, cultural, and network diversity where appropriate, while respecting privacy and anti-discrimination constraints.

## 7. Malone and Bernstein - Handbook of Collective Intelligence

### Core idea

The handbook frames collective intelligence as groups of individual actors, including people, computational agents, and organizations, acting collectively in ways that show perception, learning, judgment, coordination, problem solving, or other intelligent behavior.

It is useful because it broadens the frame beyond "teams" into an interdisciplinary design space: computer science, HCI, AI, economics, biology, psychology, organizations, and peer production.

### HUMA.I.N implications

HUMA.I.N should define what kind of collective intelligence it is trying to improve for each workflow:

- Perception: noticing signals, needs, risks, or opportunities.
- Memory: preserving and retrieving group knowledge.
- Learning: improving from feedback.
- Judgment: making better estimates or choices.
- Creation: generating ideas, plans, artifacts, or prototypes.
- Coordination: aligning people, tasks, timing, and dependencies.

The scoring framework should probably not be one universal scalar. It should be a vector of collaboration capacities tied to these functions.

## 8. Malone - Superminds

### Core idea

Malone describes "superminds" as groups of individuals acting together in ways that seem intelligent. Computers can make these superminds smarter not only through AI, but also through hyperconnectivity: connecting people to each other in richer, faster, and more scalable ways.

### HUMA.I.N implications

The strongest product framing is "computers in the group," not merely "humans in the loop." HUM should be a participant in the collaboration system that improves human-to-human collective intelligence.

This means HUM's job is to:

- Help the right people find each other.
- Help groups remember and synthesize.
- Help groups see blind spots.
- Help groups coordinate next steps.
- Help networks adapt after feedback.
- Make collaboration patterns visible enough for people to improve them.

## Proposed HUMA.I.N scoring model

Instead of one overall "collaboration potential" score, use a multi-dimensional profile. A scalar can be shown later if needed, but the underlying model should preserve the dimensions.

### 1. Task-fit capacity

How well the person fits the specific work to be done.

Signals:

- Domain knowledge.
- Relevant past contribution.
- Skill match.
- Availability.
- Context familiarity.
- Ability to create, decide, synthesize, validate, or coordinate depending on the task.

### 2. Interaction quality

How well the person helps a group think together.

Signals:

- Turn-taking balance.
- Responsiveness.
- Constructive disagreement.
- Listening and synthesis.
- Inclusion of quieter members.
- Low domination or derailment behavior.

### 3. Contribution reliability

Whether the person's contributions improve outcomes.

Signals:

- Peer uptake.
- Delivery consistency.
- Accuracy or usefulness of past inputs.
- Follow-through.
- Calibration: appropriate confidence, willingness to revise.

### 4. Network role

What role the person plays in the collaboration graph.

Signals:

- Bridge across communities.
- Access to diverse information.
- Ability to bring external insight into the group.
- Avoidance of clique-only engagement.
- Capacity to connect complementary collaborators.

### 5. Adaptive learning

Whether the person and their links improve over time.

Signals:

- Response to feedback.
- Improvement after prior collaborations.
- Flexibility across roles.
- Ability to update beliefs.
- Link-level history: which pairings or groupings repeatedly produce better results.

### 6. Motivation and incentive fit

Whether the person has a reason to participate that matches the task.

Signals:

- Stated goals.
- Intrinsic interest.
- Reputation incentives.
- Compensation needs.
- Mission alignment.
- Learning goals.

## Proposed S-Link composition logic

1. Classify the task genome.
   - Create, decide, synthesize, validate, coordinate, learn.
   - Independent collection, collaboration, consensus, expert judgment, voting, or staged workflow.

2. Select an initial set of candidate links.
   - Match on task-fit capacity.
   - Add complementary roles rather than only similar profiles.
   - Include bridge nodes for exploration when the task is ambiguous or creative.

3. Optimize group interaction conditions.
   - Avoid predicted domination by one actor.
   - Seek balanced engagement.
   - Include social sensitivity and synthesis capacity.

4. Choose the right phase pattern.
   - Exploration phase: wider, weaker, more diverse S-Links.
   - Engagement phase: tighter, trusted, coordination-oriented S-Links.
   - Decision phase: preserve independent judgment before group convergence when appropriate.

5. Add feedback and plasticity.
   - Update edge weights after collaboration.
   - Track value by context, not globally.
   - Decay stale links.
   - Create new exploratory links when networks become too closed.

6. Keep AI assistive and testable.
   - HUM recommends, explains, asks, and structures.
   - Humans retain agency over high-stakes decisions.
   - The system measures whether recommendations improved outcomes.

## Open questions for the team

- What specific outcomes should HUMA.I.N optimize: speed, quality, novelty, trust, retention, fairness, learning, or all of these?
- Are S-Links meant to connect individuals, small groups, organizations, or all three?
- What feedback signals are available after a collaboration ends?
- Which decisions are high-stakes enough to require explicit human review and appeal?
- How much of the collaboration score should be private to the user versus visible to others?
- Should the product expose raw scores, visual maps, recommendations, or coaching prompts?
- How will HUMA.I.N avoid reinforcing popularity, centrality, credential bias, or existing power networks?

## References reviewed

- Malone, T. W., Laubacher, R., and Dellarocas, C. (2010). "The Collective Intelligence Genome." MIT Sloan Management Review.
- Woolley, A. W., Chabris, C. F., Pentland, A., Hashmi, N., and Malone, T. W. (2010). "Evidence for a collective intelligence factor in the performance of human groups." Science.
- Vaccaro, M., Almaatouq, A., and Malone, T. W. (2024). "When combinations of humans and AI are useful: A systematic review and meta-analysis." Nature Human Behaviour.
- Almaatouq, A., Noriega-Campero, A., Alotaibi, A., Krafft, P. M., Moussaid, M., and Pentland, A. (2020). "Adaptive social networks promote the wisdom of crowds." PNAS.
- Pentland, A. (2012). "The New Science of Building Great Teams." Harvard Business Review.
- Pentland, A. (2013). "Beyond the Echo Chamber." Harvard Business Review.
- Malone, T. W., and Bernstein, M. S. (Eds.). (2015). Handbook of Collective Intelligence. MIT Press.
- Malone, T. W. (2018). Superminds: The Surprising Power of People and Computers Thinking Together.
