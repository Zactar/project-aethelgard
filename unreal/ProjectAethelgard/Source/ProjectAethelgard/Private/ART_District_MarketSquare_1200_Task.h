#pragma once
#include "CoreMinimal.h"
#include "StateTreeTaskBase.h"
#include "StateTreeTask_CONFRONT_THEFT.generated.h"

USTRUCT(meta = (DisplayName = "Task CONFRONT_THEFT"))
struct MYGAMEPROJECT_API FStateTreeTask_CONFRONT_THEFT : public FStateTreeTaskBase
{
    GENERATED_BODY()
    virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override
    {
        return EStateTreeRunStatus::Running;
    }
};
